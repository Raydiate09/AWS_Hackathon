from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Dict, List

from flask import Blueprint, jsonify, request

bp = Blueprint("tomtom", __name__)


def _load_route_module():
    """Dynamically load the TomTom test script so we can reuse its helpers."""
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "frontend" / "scripts" / "andrew_test.py"

    if not script_path.exists():
        raise FileNotFoundError(f"TomTom script not found at {script_path}")

    spec = importlib.util.spec_from_file_location("andrew_test", script_path)
    if spec is None or spec.loader is None:
        raise ImportError("Unable to load TomTom script")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _extract_coordinates(route_payload: Dict[str, Any]) -> List[List[float]]:
    """Flatten the legs/points data into [lng, lat] pairs for Mapbox."""
    coordinates: List[List[float]] = []
    for leg in route_payload.get("legs", []):
        for point in leg.get("points", []):
            latitude = point.get("latitude")
            longitude = point.get("longitude")
            if latitude is None or longitude is None:
                continue
            coordinates.append([float(longitude), float(latitude)])
    return coordinates


@bp.route("/tomtom-route", methods=["GET"])
def get_tomtom_route():
    """Return TomTom route data using the shared test script as the source of truth."""
    try:
        route_module = _load_route_module()
        use_live = request.args.get("live") == "true"

        if use_live and hasattr(route_module, "fetch_tomtom_route"):
            payload = route_module.fetch_tomtom_route()
        elif hasattr(route_module, "load_recorded_response"):
            payload = route_module.load_recorded_response()
        else:
            raise AttributeError("TomTom script is missing a loader function")

        coordinates = _extract_coordinates(payload)
        if not coordinates:
            return (
                jsonify({
                    "success": False,
                    "message": "Route payload did not include any coordinates."
                }),
                502,
            )

        return (
            jsonify({
                "success": True,
                "coordinates": coordinates,
                "origin": payload.get("origin"),
                "destination": payload.get("destination"),
                "summary": payload.get("route_summary"),
            }),
            200,
        )

    except Exception as exc:  # pragma: no cover - surface actionable error to caller
        return (
            jsonify({
                "success": False,
                "message": f"Failed to load TomTom route: {exc}",
            }),
            500,
        )
