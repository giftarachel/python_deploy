"""
GET /api/history  - Fetch simulations (filtered by user if token present)
DELETE /api/history/<id> - Delete a simulation
"""

from flask import Blueprint, jsonify, request
from db import get_db, _use_local
from routes.auth import verify_token

history_bp = Blueprint("history", __name__)


def _get_use_local():
    import db as db_module
    return db_module._use_local


@history_bp.route("/history", methods=["GET"])
def get_history():
    db = get_db()
    limit = int(request.args.get("limit", 20))

    user_id = None
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token:
        payload = verify_token(token)
        if payload:
            user_id = payload["sub"]

    try:
        if _get_use_local():
            # Local storage path
            cursor = db["simulations"].find()
            docs = list(cursor.sort("timestamp", -1).limit(100))
            if user_id:
                docs = [d for d in docs if d.get("user_id") == user_id]
            docs = docs[:limit]
        else:
            query = {"user_id": user_id} if user_id else {}
            docs = list(db["simulations"].find(query).sort("timestamp", -1).limit(limit))
            for d in docs:
                d["_id"] = str(d["_id"])
        return jsonify(docs), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@history_bp.route("/history/<sim_id>", methods=["DELETE"])
def delete_simulation(sim_id):
    db = get_db()
    try:
        if _get_use_local():
            result = db["simulations"].delete_one({"_id": sim_id})
        else:
            from bson import ObjectId
            result = db["simulations"].delete_one({"_id": ObjectId(sim_id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Not found"}), 404
        return jsonify({"message": "Deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
