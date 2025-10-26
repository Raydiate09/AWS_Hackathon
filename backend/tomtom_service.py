import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY", "")

def get_tomtom_route(origin_lat, origin_lng, dest_lat, dest_lng, waypoints=None, departure_time=None):
    """
    Get optimized route from TomTom API
    
    Args:
        origin_lat: Starting latitude
        origin_lng: Starting longitude
        dest_lat: Destination latitude
        dest_lng: Destination longitude
        waypoints: Optional list of waypoint locations
        departure_time: Optional ISO format datetime string for departure
    """
    if not TOMTOM_API_KEY:
        raise ValueError("TOMTOM_API_KEY not set in environment variables")
    
    # Build locations string: origin:waypoint1:waypoint2:destination
    locations = f"{origin_lat},{origin_lng}"
    
    if waypoints:
        for wp in waypoints:
            locations += f":{wp['coordinates']['lat']},{wp['coordinates']['lng']}"
    
    locations += f":{dest_lat},{dest_lng}"
    
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{locations}/json"
    
    params = {
        "key": TOMTOM_API_KEY,
        "traffic": "true",
        "travelMode": "car",
        "computeBestOrder": "true"  # Optimize waypoint order
    }
    
    # Add departure time if provided for more accurate traffic data
    if departure_time:
        params["departAt"] = departure_time
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract coordinates from response
        coordinates = []
        if "routes" in data and len(data["routes"]) > 0:
            route = data["routes"][0]
            for leg in route.get("legs", []):
                for point in leg.get("points", []):
                    coordinates.append([
                        point.get("longitude"),
                        point.get("latitude")
                    ])
        
        return {
            "success": True,
            "coordinates": coordinates,
            "summary": data.get("routes", [{}])[0].get("summary", {}),
            "raw_data": data
        }
        
    except Exception as e:
        print(f"TomTom API error: {e}")
        return {
            "success": False,
            "error": str(e),
            "coordinates": []
        }
