from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


def _load_tomtom_module():
    """Load the utility script that interacts with the TomTom API."""
    scripts_dir = Path(__file__).resolve().parent / "scripts"
    script_path = scripts_dir / "andrew_test.py"

    if not script_path.exists():
        raise FileNotFoundError(f"TomTom helper script is missing at {script_path}")

    spec = importlib.util.spec_from_file_location("andrew_test", script_path)
    if spec is None or spec.loader is None:
        raise ImportError("Unable to load the TomTom helper script")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _extract_coordinates(route_payload: Dict[str, Any]) -> List[List[float]]:
    """Convert TomTom leg/point data into Mapbox-friendly [lng, lat] pairs."""
    coordinates: List[List[float]] = []

    for leg in route_payload.get("legs", []):
        for point in leg.get("points", []):
            latitude = point.get("latitude")
            longitude = point.get("longitude")
            if latitude is None or longitude is None:
                continue
            coordinates.append([float(longitude), float(latitude)])

    return coordinates


def _load_recorded_payload(module: Any) -> Dict[str, Any]:
    """Attempt to reuse the script's loader, falling back to a local file."""
    try:
        return module.load_recorded_response()
    except FileNotFoundError:
        fallback_path = Path(__file__).resolve().parent / "recorded_response.json"
        if not fallback_path.exists():
            raise
        with fallback_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)


@app.route("/api/tomtom-route", methods=["GET"])
def tomtom_route():
    """Provide route coordinates sourced from the TomTom helper script."""
    try:
        module = _load_tomtom_module()
        use_live = request.args.get("live", "").lower() == "true"

        if use_live and hasattr(module, "fetch_tomtom_route"):
            payload = module.fetch_tomtom_route()  # type: ignore[attr-defined]
        else:
            payload = _load_recorded_payload(module)

        coordinates = _extract_coordinates(payload)
        if not coordinates:
            return jsonify({"success": False, "message": "No coordinates returned from TomTom data."}), 502

        return jsonify(
            {
                "success": True,
                "coordinates": coordinates,
                "origin": payload.get("origin"),
                "destination": payload.get("destination"),
                "summary": payload.get("route_summary"),
            }
        )
    except Exception as exc:  # pragma: no cover - expose diagnostic detail to caller
        return jsonify({"success": False, "message": f"Failed to retrieve TomTom route: {exc}"}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5003"))
    app.run(host="0.0.0.0", port=port, debug=True)
