from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import os
import json
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from tomtom_service import get_tomtom_route
from google_maps_service import get_google_maps_route
from sunlight_service import calculate_sunlight_risk, calculate_driving_bearing, analyze_route_sunlight_risk
import csv

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

@app.route('/api/crash-data', methods=['GET'])
def get_crash_data():
    try:
        with open('../crashdata2022-present.csv', 'r') as f:
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