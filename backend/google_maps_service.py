import os
import requests
from datetime import datetime, timezone
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")


def _decode_polyline(polyline: str) -> List[List[float]]:
    """Decode a Google encoded polyline string into a list of [lng, lat] pairs."""
    index = 0
    length = len(polyline)
    lat = 0
    lng = 0
    coordinates: List[List[float]] = []

    while index < length:
        shift = 0
        result = 0
        while True:
            if index >= length:
                break
            b = ord(polyline[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        delta_lat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += delta_lat

        shift = 0
        result = 0
        while True:
            if index >= length:
                break
            b = ord(polyline[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        delta_lng = ~(result >> 1) if (result & 1) else (result >> 1)
        lng += delta_lng

        coordinates.append([lng / 1e5, lat / 1e5])

    return coordinates


def _format_waypoints(waypoints: Optional[List[dict]]) -> Optional[str]:
    """Format waypoints for the Directions API, enabling waypoint optimization."""
    if not waypoints:
        return None

    formatted_points = []
    for wp in waypoints:
        coords = wp.get("coordinates", {})
        lat = coords.get("lat")
        lng = coords.get("lng")
        if lat is None or lng is None:
            continue
        formatted_points.append(f"{lat},{lng}")

    if not formatted_points:
        return None

    return "optimize:true|" + "|".join(formatted_points)


def _format_departure_time(departure_time: Optional[str]) -> Optional[str]:
    """Convert ISO datetime string to seconds since epoch for the Directions API."""
    if not departure_time:
        return None

    if departure_time.lower() == "now":
        return "now"

    try:
        # Support both "YYYY-MM-DDTHH:MM:SS" and the same with a trailing "Z" or timezone
        if departure_time.endswith("Z"):
            dt = datetime.fromisoformat(departure_time.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(departure_time)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return str(int(dt.timestamp()))
    except ValueError:
        # Fall back to letting the API handle invalid times by omitting the parameter
        return None


def get_google_maps_route(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    waypoints: Optional[List[dict]] = None,
    departure_time: Optional[str] = None,
    traffic_model: str = "best_guess"
):
    """Get an optimized driving route from the Google Maps Directions API."""
    if not GOOGLE_MAPS_API_KEY:
        raise ValueError("GOOGLE_MAPS_API_KEY not set in environment variables")

    params = {
        "origin": f"{origin_lat},{origin_lng}",
        "destination": f"{dest_lat},{dest_lng}",
        "key": GOOGLE_MAPS_API_KEY,
        "mode": "driving",
    }

    waypoint_param = _format_waypoints(waypoints)
    if waypoint_param:
        params["waypoints"] = waypoint_param

    depart_param = _format_departure_time(departure_time)
    if depart_param:
        params["departure_time"] = depart_param
        params["traffic_model"] = traffic_model

    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/directions/json",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        status = data.get("status")
        if status != "OK":
            error_message = data.get("error_message", status or "Unknown error")
            return {
                "success": False,
                "error": error_message,
                "coordinates": [],
                "segments": [],
                "raw_data": data
            }

        route = data.get("routes", [{}])[0]
        overview_polyline = route.get("overview_polyline", {}).get("points", "")
        coordinates = _decode_polyline(overview_polyline) if overview_polyline else []

        segments = []
        legs_data = []
        for leg_index, leg in enumerate(route.get("legs", [])):
            steps = leg.get("steps", [])
            leg_coordinates: List[List[float]] = []
            for step_index, step in enumerate(steps):
                polyline_points = step.get("polyline", {}).get("points", "")
                step_coords = _decode_polyline(polyline_points) if polyline_points else []
                if step_coords:
                    leg_coordinates.extend(step_coords)
                segments.append({
                    "coordinates": step_coords,
                    "distance_meters": step.get("distance", {}).get("value", 0),
                    "duration_seconds": step.get("duration", {}).get("value", 0),
                    "duration_in_traffic_seconds": step.get("duration_in_traffic", {}).get("value"),
                    "instruction": step.get("html_instructions", ""),
                    "travel_mode": step.get("travel_mode", "DRIVING"),
                    "step_index": step_index,
                    "leg_index": leg_index
                })
            legs_data.append({
                "leg_index": leg_index,
                "start_address": leg.get("start_address", ""),
                "end_address": leg.get("end_address", ""),
                "start_location": leg.get("start_location", {}),
                "end_location": leg.get("end_location", {}),
                "distance_meters": leg.get("distance", {}).get("value", 0),
                "duration_seconds": leg.get("duration", {}).get("value", 0),
                "duration_in_traffic_seconds": leg.get("duration_in_traffic", {}).get("value"),
                "steps_count": len(steps),
                "coordinates": leg_coordinates
            })

        summary = {
            "distance_meters": sum(leg.get("distance", {}).get("value", 0) for leg in route.get("legs", [])),
            "duration_seconds": sum(leg.get("duration", {}).get("value", 0) for leg in route.get("legs", [])),
            "duration_in_traffic_seconds": sum(
                leg.get("duration_in_traffic", {}).get("value", leg.get("duration", {}).get("value", 0))
                for leg in route.get("legs", [])
            ),
            "waypoint_order": route.get("waypoint_order", [])
        }

        return {
            "success": True,
            "coordinates": coordinates,
            "legs": legs_data,
            "segments": segments,
            "summary": summary,
            "raw_data": data
        }

    except Exception as exc:
        print(f"Google Maps Directions API error: {exc}")
        return {
            "success": False,
            "error": str(exc),
            "coordinates": [],
            "legs": [],
            "segments": []
        }
