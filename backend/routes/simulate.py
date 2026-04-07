"""
POST /api/simulate
Accepts suspension config + force input, runs matrix solver, stores in MongoDB.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from solver import solve_force_distribution
from db import get_db
from routes.auth import verify_token

simulate_bp = Blueprint("simulate", __name__)


@simulate_bp.route("/simulate", methods=["POST"])
def simulate():
    data = request.get_json()

    # Optional auth — attach user_id if token present
    user_id = None
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token:
        payload = verify_token(token)
        if payload:
            user_id = payload["sub"]

    links = data.get("links", [])
    external_force = float(data.get("external_force", 0))
    force_type = data.get("force_type", "bump")

    if not links or len(links) < 1:
        return jsonify({"error": "At least one link is required"}), 400
    if external_force <= 0:
        return jsonify({"error": "External force must be positive"}), 400

    angles = [float(l["angle"]) for l in links]
    lengths = [float(l["length"]) for l in links]

    # Core matrix solver (Direction Cosine Matrix + NumPy)
    result = solve_force_distribution(angles, external_force, force_type)

    document = {
        "user_id": user_id,
        "links": links,
        "external_force": external_force,
        "force_type": force_type,
        "results": result["link_forces"],
        "direction_cosine_matrix": result["direction_cosine_matrix"],
        "external_force_vector": result["external_force_vector"],
        "method": result["method"],
        "residual": result["residual"],
        "max_stress_link": result["max_stress_link"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        db = get_db()
        inserted = db["simulations"].insert_one(document)
        document["_id"] = str(inserted.inserted_id)
        return jsonify(document), 200
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)[:120]}"}), 500
