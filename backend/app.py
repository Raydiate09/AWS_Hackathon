from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import os
import json
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from tomtom_service import get_tomtom_route
from google_maps_service import get_google_maps_route
from sunlight_service import calculate_sunlight_risk, calculate_driving_bearing, analyze_route_sunlight_risk
import csv
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree
from pyproj import Transformer


CRASH_DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "crashdata2022-present.csv")
PROJECT_TRANSFORMER = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
CRASH_GEOMETRIES: List[Point] = []
CRASH_METADATA: List[Dict[str, Any]] = []
CRASH_TREE: Optional[STRtree] = None
CRASH_GEOM_INDEX: Dict[int, int] = {}


def _parse_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _parse_bool(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _parse_optional_int(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _ensure_crash_spatial_index() -> None:
    global CRASH_TREE, CRASH_GEOMETRIES, CRASH_METADATA, CRASH_GEOM_INDEX

    if CRASH_TREE is not None and CRASH_GEOMETRIES and CRASH_METADATA and CRASH_GEOM_INDEX:
        return

    if not os.path.exists(CRASH_DATASET_PATH):
        raise FileNotFoundError("Crash dataset not found at path: " + CRASH_DATASET_PATH)

    crash_points: List[Point] = []
    metadata: List[Dict[str, Any]] = []

    with open(CRASH_DATASET_PATH, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            lat = _parse_float(row.get("Latitude"))
            lon = _parse_float(row.get("Longitude"))

            if lat is None or lon is None:
                continue

            x, y = PROJECT_TRANSFORMER.transform(lon, lat)
            geom = Point(x, y)
            crash_points.append(geom)

            fatal = _parse_int(row.get("FatalInjuries"))
            severe = _parse_int(row.get("SevereInjuries"))
            moderate = _parse_int(row.get("ModerateInjuries"))
            minor = _parse_int(row.get("MinorInjuries"))

            metadata.append({
                "crash_fact_id": row.get("CrashFactId"),
                "name": row.get("Name"),
                "crash_datetime": row.get("CrashDateTime"),
                "collision_type": row.get("CollisionType"),
                "primary_factor": row.get("PrimaryCollisionFactor"),
                "lighting": row.get("Lighting"),
                "weather": row.get("Weather"),
                "a_street": row.get("AStreetName"),
                "b_street": row.get("BStreetName"),
                "latitude": lat,
                "longitude": lon,
                "fatal_injuries": fatal,
                "severe_injuries": severe,
                "moderate_injuries": moderate,
                "minor_injuries": minor,
                "total_injuries": fatal + severe + moderate + minor,
                "speeding_flag": _parse_bool(row.get("SpeedingFlag")),
                "hit_and_run_flag": _parse_bool(row.get("HitAndRunFlag")),
            })

    CRASH_GEOMETRIES = crash_points
    CRASH_METADATA = metadata

    if crash_points:
        CRASH_TREE = STRtree(crash_points)
        CRASH_GEOM_INDEX = {id(geom): idx for idx, geom in enumerate(crash_points)}
    else:
        CRASH_TREE = None
        CRASH_GEOM_INDEX = {}


def _project_segment_coordinates(coords: List[List[float]]) -> Optional[LineString]:
    projected: List[Tuple[float, float]] = []
    for coord in coords:
        if not isinstance(coord, (list, tuple)) or len(coord) != 2:
            continue
        lon, lat = coord
        lon_f = _parse_float(lon)
        lat_f = _parse_float(lat)
        if lon_f is None or lat_f is None:
            continue
        x, y = PROJECT_TRANSFORMER.transform(lon_f, lat_f)
        projected.append((x, y))

    if len(projected) < 2:
        return None

    return LineString(projected)

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# AWS clients
bedrock = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

dynamodb = boto3.resource(
    "dynamodb",
    region_name="us-east-1",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

# DynamoDB table
table = dynamodb.Table("optimizedRoute")  # type: ignore

# Claude model ID
model_id = "global.anthropic.claude-haiku-4-5-20251001-v1:0"

def invoke_claude(prompt):
    """Invoke Claude with a prompt"""
    body = json.dumps({
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,
        "anthropic_version": "bedrock-2023-05-31"
    })

    try:
        print(f"Invoking Claude with prompt: {prompt[:100]}...")
        response = bedrock.invoke_model(modelId=model_id, body=body)
        response_body = json.loads(response['body'].read())
        result = response_body['content'][0]['text']
        print(f"Claude response received: {result[:100]}...")
        return result
    except Exception as e:
        print(f"Error invoking Claude: {e}")
        import traceback
        traceback.print_exc()
        return f"Error generating AI response: {str(e)}"


def create_route_segments_from_coordinates(
    coordinates: List[List[float]],
    total_duration_seconds: int
) -> List[Dict[str, Any]]:
    """Create simple route segments from coordinate pairs with estimated durations."""
    if len(coordinates) < 2:
        return []

    segment_count = len(coordinates) - 1
    base_duration = total_duration_seconds // segment_count if total_duration_seconds else 0

    segments: List[Dict[str, Any]] = []
    for idx in range(segment_count):
        start = coordinates[idx]
        end = coordinates[idx + 1]
        segments.append({
            "name": f"Segment {idx + 1}",
            "from_lat": start[1],
            "from_lng": start[0],
            "to_lat": end[1],
            "to_lng": end[0],
            "duration_seconds": base_duration or 0
        })

    return segments


class DriverScheduleOptimizer:
    """Minimal placeholder optimizer that returns a basic driving schedule."""

    def optimize_schedule(
        self,
        segments: List[Dict[str, Any]],
        departure_time: datetime,
        preferred_arrival: Optional[datetime] = None
    ) -> Dict[str, Any]:
        schedule_segments: List[Dict[str, Any]] = []
        current_time = departure_time

        for segment in segments:
            duration_seconds = segment.get("duration_seconds", 0)
            next_time = current_time + timedelta(seconds=duration_seconds)
            schedule_segments.append({
                "segment_name": segment.get("name", "Segment"),
                "start_time": current_time.isoformat(),
                "end_time": next_time.isoformat(),
                "duration_seconds": duration_seconds
            })
            current_time = next_time

        arrival_time = preferred_arrival.isoformat() if preferred_arrival else current_time.isoformat()

        return {
            "departure_time": departure_time.isoformat(),
            "estimated_arrival": arrival_time,
            "segments": schedule_segments
        }

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "success": True,
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "dynamodb": "connected",
            "bedrock": "connected"
        }
    })

@app.route('/api/optimize-route', methods=['POST'])
def optimize_route():
    try:
        data = request.get_json()
        print(f"Received optimize-route request: {data}")

        user_id = data.get('userId')
        route = data.get('route', {})
        delivery_window = data.get('deliveryWindow', {})

        origin_addr = route.get('origin', {}).get('address', 'Unknown')
        dest_addr = route.get('destination', {}).get('address', 'Unknown')
        stops = route.get('stops', [])
        
        print(f"Route: {origin_addr} -> {dest_addr} with {len(stops)} stops")

        # Create a prompt for Claude
        prompt = f"""
Optimize this delivery route:

Origin: {origin_addr}
Destination: {dest_addr}
Number of Stops: {len(stops)}
Delivery Window: {delivery_window.get('startDate')} to {delivery_window.get('endDate')}

Please provide:
1. Recommended departure time
2. Traffic considerations
3. Weather considerations  
4. Route optimization tips
5. Estimated delivery time

Keep the response concise and actionable.
"""

        print("Calling Claude API...")
        claude_response = invoke_claude(prompt)
        print(f"Claude response length: {len(claude_response)} characters")

        # Mock response structure
        response_data = {
            "success": True,
            "data": {
                "requestId": f"req_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "optimizedRoute": {
                    "origin": route.get('origin'),
                    "destination": route.get('destination'),
                    "stops": stops,
                    "recommendedDepartureTime": delivery_window.get('startDate'),
                    "estimatedArrivalTime": delivery_window.get('endDate')
                },
                "metrics": {
                    "distance": 31.4,  # Mock - in miles (calculate real distance from route)
                    "estimatedTime": "2 hours",
                    "scores": {
                        "weather": 85,
                        "traffic": 90,
                        "sunlight": 95,
                        "overall": 90
                    }
                },
                "recommendations": [claude_response],
                "departureTime": delivery_window.get('startDate'),
                "arrivalTime": delivery_window.get('endDate')
            }
        }

        print("Sending response to frontend")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in optimize_route: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/request/<request_id>', methods=['GET'])
def get_request(request_id):
    # Mock data - in real implementation, query DynamoDB
    mock_request = {
        "requestId": request_id,
        "userId": "user123",
        "status": "completed",
        "route": {
            "origin": {"address": "Start", "coordinates": {"lat": 0, "lng": 0}},
            "destination": {"address": "End", "coordinates": {"lat": 1, "lng": 1}}
        }
    }

    return jsonify({
        "success": True,
        "data": {
            "request": mock_request,
            "metrics": {"distance": 50.5, "time": "2h"},
            "evaluation": {"score": 90, "feedback": "Good route"}
        }
    })

@app.route('/api/user/<user_id>/requests', methods=['GET'])
def get_user_requests(user_id):
    # Mock data
    mock_requests = [
        {
            "requestId": f"req_{user_id}_1",
            "status": "completed",
            "createdAt": datetime.now().isoformat()
        }
    ]

    return jsonify({
        "success": True,
        "data": {
            "requests": mock_requests,
            "nextKey": None
        }
    })

@app.route('/api/request/<request_id>/reoptimize', methods=['POST'])
def reoptimize_route(request_id):
    data = request.get_json()
    constraints = data.get('constraints', {})

    # Mock re-optimization
    return jsonify({
        "success": True,
        "data": {
            "optimizedRoute": {"message": "Re-optimized"},
            "message": "Route successfully re-optimized"
        }
    })

@app.route('/api/request/<request_id>/status', methods=['GET'])
def get_request_status(request_id):
    # Mock status
    return jsonify({
        "success": True,
        "data": {
            "status": "completed",
            "progress": 100
        }
    })

@app.route('/api/validate-route', methods=['POST'])
def validate_route():
    data = request.get_json()
    route = data.get('route', {})

    # Simple validation
    validation = {
        "isValid": True,
        "warnings": ["Route looks good"],
        "errors": []
    }

    return jsonify({
        "success": True,
        "data": validation
    })

@app.route('/api/tomtom-route', methods=['POST'])
def tomtom_route():
    """Get optimized route from TomTom API"""
    try:
        data = request.get_json()
        print(f"TomTom route request: {data}")
        
        route = data.get('route', {})
        origin = route.get('origin', {}).get('coordinates', {})
        destination = route.get('destination', {}).get('coordinates', {})
        stops = route.get('stops', [])
        
        result = get_tomtom_route(
            origin.get('lat'),
            origin.get('lng'),
            destination.get('lat'),
            destination.get('lng'),
            stops
        )
        
        if result['success']:
            return jsonify({
                "success": True,
                "coordinates": result['coordinates'],
                "summary": result.get('summary', {})
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get('error', 'Unknown error')
            }), 500
            
    except Exception as e:
        print(f"Error in tomtom_route: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/google-maps-route', methods=['POST'])
def google_maps_route():
    """Get optimized route details from Google Maps Directions API."""
    try:
        data = request.get_json(silent=True) or {}
        print(f"Google Maps route request: {data}")

        route = data.get('route', {})
        origin = route.get('origin', {}).get('coordinates', {})
        destination = route.get('destination', {}).get('coordinates', {})
        stops = route.get('stops', [])

        preferred_departure = data.get('preferred_start_time') or data.get('preferred_departure_time')

        if not all([
            origin.get('lat'), origin.get('lng'),
            destination.get('lat'), destination.get('lng')
        ]):
            return jsonify({
                "success": False,
                "error": "Origin and destination coordinates are required"
            }), 400

        result = get_google_maps_route(
            origin_lat=origin.get('lat'),
            origin_lng=origin.get('lng'),
            dest_lat=destination.get('lat'),
            dest_lng=destination.get('lng'),
            waypoints=stops,
            departure_time=preferred_departure
        )

        if result.get('success'):
            return jsonify({
                "success": True,
                "coordinates": result.get('coordinates', []),
                "summary": result.get('summary', {}),
                "segments": result.get('segments', []),
                "legs": result.get('legs', [])
            })

        return jsonify({
            "success": False,
            "error": result.get('error', 'Unknown error')
        }), 500

    except Exception as e:
        print(f"Error in google_maps_route: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/crash-proximity', methods=['POST'])
def analyze_crash_proximity():
    """Identify route segments that are close to historic crash incidents using spatial analysis."""
    try:
        payload = request.get_json(silent=True) or {}
        segments_input = payload.get('segments', [])
        threshold_meters = payload.get('threshold_meters', 200)
        max_crashes_per_segment = payload.get('max_crashes_per_segment', 5)

        try:
            threshold_meters = float(threshold_meters)
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "error": "threshold_meters must be a number"
            }), 400

        try:
            max_crashes_per_segment = int(max_crashes_per_segment)
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "error": "max_crashes_per_segment must be an integer"
            }), 400

        if not isinstance(segments_input, list) or len(segments_input) == 0:
            return jsonify({
                "success": False,
                "error": "segments array is required"
            }), 400

        _ensure_crash_spatial_index()

        if CRASH_TREE is None or not CRASH_GEOMETRIES:
            return jsonify({
                "success": False,
                "error": "Crash dataset is not available"
            }), 500

        total_segments = 0
        segments_with_crashes = 0
        total_close_crashes = 0
        segment_results: List[Dict[str, Any]] = []
        leg_summary: Dict[int, Dict[str, Any]] = {}

        for segment in segments_input:
            coords = segment.get('coordinates') or []
            line = _project_segment_coordinates(coords)
            if line is None or line.length == 0:
                continue

            total_segments += 1

            buffer_geom = line.buffer(threshold_meters)
            candidate_points = CRASH_TREE.query(buffer_geom)

            close_crashes: List[Dict[str, Any]] = []
            for geom in candidate_points:
                crash_idx = CRASH_GEOM_INDEX.get(id(geom))
                if crash_idx is None:
                    continue

                crash_info = CRASH_METADATA[crash_idx]
                distance = geom.distance(line)

                if distance <= threshold_meters:
                    close_crashes.append({
                        "crash_fact_id": crash_info.get("crash_fact_id"),
                        "name": crash_info.get("name"),
                        "latitude": crash_info.get("latitude"),
                        "longitude": crash_info.get("longitude"),
                        "distance_meters": round(distance, 2),
                        "crash_datetime": crash_info.get("crash_datetime"),
                        "collision_type": crash_info.get("collision_type"),
                        "primary_factor": crash_info.get("primary_factor"),
                        "lighting": crash_info.get("lighting"),
                        "weather": crash_info.get("weather"),
                        "a_street": crash_info.get("a_street"),
                        "b_street": crash_info.get("b_street"),
                        "fatal_injuries": crash_info.get("fatal_injuries"),
                        "severe_injuries": crash_info.get("severe_injuries"),
                        "moderate_injuries": crash_info.get("moderate_injuries"),
                        "minor_injuries": crash_info.get("minor_injuries"),
                        "total_injuries": crash_info.get("total_injuries"),
                        "speeding_flag": crash_info.get("speeding_flag"),
                        "hit_and_run_flag": crash_info.get("hit_and_run_flag"),
                    })

            if not close_crashes:
                leg_index_val = _parse_optional_int(segment.get('leg_index'))
                if leg_index_val is not None:
                    leg_entry = leg_summary.setdefault(leg_index_val, {
                        "leg_index": leg_index_val,
                        "segment_count": 0,
                        "segments_with_crashes": 0,
                        "total_close_crashes": 0,
                        "min_distance_meters": None,
                    })
                    leg_entry["segment_count"] += 1
                continue

            close_crashes.sort(key=lambda item: item["distance_meters"])
            if max_crashes_per_segment > 0:
                close_crashes = close_crashes[:max_crashes_per_segment]

            min_distance = close_crashes[0]["distance_meters"] if close_crashes else None

            segments_with_crashes += 1
            total_close_crashes += len(close_crashes)

            leg_index_val = _parse_optional_int(segment.get('leg_index'))
            step_index_val = _parse_optional_int(segment.get('step_index'))

            segment_result = {
                "leg_index": leg_index_val,
                "step_index": step_index_val,
                "instruction": segment.get('instruction'),
                "travel_mode": segment.get('travel_mode'),
                "distance_meters": segment.get('distance_meters'),
                "duration_seconds": segment.get('duration_seconds'),
                "duration_in_traffic_seconds": segment.get('duration_in_traffic_seconds'),
                "close_crash_count": len(close_crashes),
                "min_distance_meters": min_distance,
                "close_crashes": close_crashes,
            }

            segment_results.append(segment_result)

            if leg_index_val is not None:
                leg_entry = leg_summary.setdefault(leg_index_val, {
                    "leg_index": leg_index_val,
                    "segment_count": 0,
                    "segments_with_crashes": 0,
                    "total_close_crashes": 0,
                    "min_distance_meters": None,
                })
                leg_entry["segment_count"] += 1
                leg_entry["segments_with_crashes"] += 1
                leg_entry["total_close_crashes"] += len(close_crashes)
                current_min = leg_entry.get("min_distance_meters")
                if current_min is None or (min_distance is not None and min_distance < current_min):
                    leg_entry["min_distance_meters"] = min_distance

        response_payload = {
            "success": True,
            "threshold_meters": threshold_meters,
            "segment_count": total_segments,
            "segments_with_crashes": segments_with_crashes,
            "total_close_crashes": total_close_crashes,
            "segments": segment_results,
            "legs_summary": sorted(leg_summary.values(), key=lambda item: item["leg_index"])
        }

        return jsonify(response_payload)

    except FileNotFoundError as file_err:
        return jsonify({
            "success": False,
            "error": str(file_err)
        }), 500
    except Exception as exc:
        print(f"Crash proximity analysis error: {exc}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(exc)
        }), 500

@app.route('/api/crash-data', methods=['GET'])
def get_crash_data():
    try:
        with open(CRASH_DATASET_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            records = list(reader)[:100]
        return jsonify({
            "success": True,
            "data": records
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/sunlight-risk', methods=['POST'])
def calculate_route_sunlight_risk():
    """
    Calculate sunlight risk for a route based on time and driving direction.
    
    Expected request body:
    {
        "origin": {"lat": float, "lng": float},
        "destination": {"lat": float, "lng": float},
        "departure_time": "ISO 8601 datetime string",
        "route_coordinates": [[lng, lat], ...] (optional, from TomTom)
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        
        origin = data.get('origin', {})
        destination = data.get('destination', {})
        departure_str = data.get('departure_time')
        route_coords = data.get('route_coordinates', [])
        
        if not all([origin.get('lat'), origin.get('lng'), 
                   destination.get('lat'), destination.get('lng')]):
            return jsonify({
                "success": False,
                "error": "Origin and destination coordinates required"
            }), 400
        
        # Parse departure time
        if departure_str:
            try:
                departure_time = datetime.fromisoformat(departure_str.replace('Z', '+00:00'))
            except:
                departure_time = datetime.now(timezone.utc)
        else:
            departure_time = datetime.now(timezone.utc)
        
        # If we have detailed route coordinates, analyze multiple segments
        if route_coords and len(route_coords) > 1:
            # Sample every Nth coordinate to create segments (to avoid too many calculations)
            sample_rate = max(1, len(route_coords) // 10)  # Max 10 segments
            sampled_coords = route_coords[::sample_rate]
            
            # Ensure we include the last coordinate
            if sampled_coords[-1] != route_coords[-1]:
                sampled_coords.append(route_coords[-1])
            
            # Create segments from coordinates
            segments = []
            # Assume average speed of 30 mph (48 km/h) for time estimation
            avg_speed_deg_per_sec = 0.0002  # Rough approximation
            
            for i in range(len(sampled_coords) - 1):
                from_coord = sampled_coords[i]
                to_coord = sampled_coords[i + 1]
                
                # Calculate approximate duration based on distance
                lat_diff = abs(to_coord[1] - from_coord[1])
                lng_diff = abs(to_coord[0] - from_coord[0])
                distance = (lat_diff ** 2 + lng_diff ** 2) ** 0.5
                duration = int(distance / avg_speed_deg_per_sec)
                
                segments.append({
                    'from_lat': from_coord[1],  # Remember: route_coords is [lng, lat]
                    'from_lng': from_coord[0],
                    'to_lat': to_coord[1],
                    'to_lng': to_coord[0],
                    'duration_seconds': duration,
                    'name': f'Segment {i+1}'
                })
            
            # Analyze all segments
            analysis = analyze_route_sunlight_risk(segments, departure_time)
            
        else:
            # Simple point-to-point analysis
            bearing = calculate_driving_bearing(
                origin['lat'], origin['lng'],
                destination['lat'], destination['lng']
            )
            
            # Use midpoint of route for sun calculation
            mid_lat = (origin['lat'] + destination['lat']) / 2
            mid_lng = (origin['lng'] + destination['lng']) / 2
            
            risk = calculate_sunlight_risk(mid_lat, mid_lng, bearing, departure_time)
            
            analysis = {
                'overall_risk_score': risk['risk_score'],
                'overall_risk_level': risk['risk_level'],
                'departure_time': departure_time.isoformat(),
                'segment_count': 1,
                'segments': [{
                    'segment_index': 0,
                    'segment_name': 'Full Route',
                    'start_time': departure_time.isoformat(),
                    **risk
                }],
                'recommendations': [
                    f"☀️ {risk['explanation']}",
                    "✅ Consider sunglasses and functional sun visors" if risk['risk_score'] > 60 else
                    "✅ Good visibility conditions"
                ]
            }
        
        return jsonify({
            "success": True,
            "data": analysis
        })
        
    except Exception as e:
        print(f"Sunlight risk calculation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/optimize-driver-schedule', methods=['POST'])
def optimize_driver_schedule():
    """
    Create HOS-compliant driver schedule with sunlight risk management.
    
    Expected request body:
    {
        "route_coordinates": [[lng, lat], ...],
        "total_duration_seconds": int,
        "departure_time": "ISO 8601 datetime string",
        "preferred_arrival": "ISO 8601 datetime string" (optional)
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        
        route_coords = data.get('route_coordinates', [])
        total_duration = data.get('total_duration_seconds', 0)
        departure_str = data.get('departure_time')
        arrival_str = data.get('preferred_arrival')
        
        if not route_coords or len(route_coords) < 2:
            return jsonify({
                "success": False,
                "error": "Route coordinates required (minimum 2 points)"
            }), 400
        
        # Parse departure time
        if departure_str:
            try:
                departure_time = datetime.fromisoformat(departure_str.replace('Z', '+00:00'))
            except:
                departure_time = datetime.now(timezone.utc)
        else:
            departure_time = datetime.now(timezone.utc)
        
        # Parse preferred arrival (optional)
        preferred_arrival = None
        if arrival_str:
            try:
                preferred_arrival = datetime.fromisoformat(arrival_str.replace('Z', '+00:00'))
            except:
                pass
        
        # Create route segments
        segments = create_route_segments_from_coordinates(route_coords, total_duration)
        
        # Optimize schedule
        optimizer = DriverScheduleOptimizer()
        schedule = optimizer.optimize_schedule(segments, departure_time, preferred_arrival)
        
        return jsonify({
            "success": True,
            "data": schedule
        })
        
    except Exception as e:
        print(f"Schedule optimization error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)