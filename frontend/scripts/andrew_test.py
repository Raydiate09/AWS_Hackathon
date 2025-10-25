"""Utility script for exercising the TomTom Routing API without the backend service."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict

import requests

# Coordinates: San Francisco International Airport to Santa Clara University
_ORIGIN = (37.62131, -122.37896)
_DESTINATION = (37.34964, -121.93990)
_TOMTOM_BASE_URL = "https://api.tomtom.com/routing/1/calculateRoute/"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RECORDED_RESPONSE_PATH = PROJECT_ROOT / "recorded_response.json"


def fetch_tomtom_route(api_key: str | None = None) -> Dict[str, Any]:
    """Fetch TomTom route data between the defined origin and destination."""
    if not api_key:
        api_key = os.getenv("TOMTOM_API_KEY")

    if not api_key:
        raise RuntimeError(
            "TomTom API key is missing. Set TOMTOM_API_KEY in your environment or pass it explicitly."
        )

    path = f"{_ORIGIN[0]},{_ORIGIN[1]}:{_DESTINATION[0]},{_DESTINATION[1]}/json"
    params = {"key": api_key}

    try:
        response = requests.get(f"{_TOMTOM_BASE_URL}{path}", params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:  # pragma: no cover - best effort diagnostics
        status_code = exc.response.status_code if exc.response else "unknown"
        detail = exc.response.text if exc.response else str(exc)
        raise RuntimeError(f"TomTom API returned HTTP {status_code}: {detail}") from exc
    except requests.exceptions.RequestException as exc:  # pragma: no cover - best effort diagnostics
        raise RuntimeError(f"Failed to reach TomTom API: {exc}") from exc

    data = response.json()
    routes = data.get("routes", [])
    if not routes:
        raise RuntimeError("TomTom API response did not contain route data.")

    primary_route = routes[0]
    summary = primary_route.get("summary", {})

    return {
        "success": True,
        "origin": {
            "name": "San Francisco International Airport",
            "latitude": _ORIGIN[0],
            "longitude": _ORIGIN[1],
        },
        "destination": {
            "name": "Santa Clara University",
            "latitude": _DESTINATION[0],
            "longitude": _DESTINATION[1],
        },
        "route_summary": {
            "length_in_meters": summary.get("lengthInMeters"),
            "travel_time_in_seconds": summary.get("travelTimeInSeconds"),
            "traffic_delay_in_seconds": summary.get("trafficDelayInSeconds"),
            "departure_time": summary.get("departureTime"),
            "arrival_time": summary.get("arrivalTime"),
        },
        "legs": primary_route.get("legs", []),
        "raw": primary_route,
    }


def load_recorded_response() -> Dict[str, Any]:
    """Load the recorded response from disk."""
    with RECORDED_RESPONSE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_recorded_response(data: Dict[str, Any]) -> None:
    """Persist the provided data to the recorded response file."""
    RECORDED_RESPONSE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def test_tomtom_route(use_recorded: bool = True) -> None:
    """Exercise the TomTom API call, optionally using a recorded response."""
    if use_recorded:
        if not RECORDED_RESPONSE_PATH.exists():
            print("❌ Recorded response file not found. Run with --live to fetch a new response.")
            return
        data = load_recorded_response()
        print("Using recorded response from recorded_response.json")
    else:
        try:
            data = fetch_tomtom_route()
        except RuntimeError as exc:
            print(f"❌ Test failed: {exc}")
            return
        save_recorded_response(data)
        print("Response saved to recorded_response.json")

    if data.get("success"):
        print("✅ Test passed: TomTom route call returned success.")
        print("Origin:", data.get("origin", {}).get("name"))
        print("Destination:", data.get("destination", {}).get("name"))
        print("Route Summary:")
        summary = data.get("route_summary", {})
        print(f"  - Length: {summary.get('length_in_meters')} meters")
        print(f"  - Travel Time: {summary.get('travel_time_in_seconds')} seconds")
        print(f"  - Traffic Delay: {summary.get('traffic_delay_in_seconds')} seconds")
        print("Full response:")
        print(json.dumps(data, indent=2))
    else:
        print("❌ Test failed: Call returned success=False")
        print("Message:", data.get("message"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Test the TomTom route API call without the backend service.")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Fetch data from the TomTom API instead of using the recorded response.",
    )
    args = parser.parse_args()

    print("Testing TomTom route call...")
    test_tomtom_route(use_recorded=not args.live)


if __name__ == "__main__":
    main()
