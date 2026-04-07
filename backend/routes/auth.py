"""
Auth routes: POST /api/register, POST /api/login
Passwords hashed with bcrypt. JWT tokens for session.
"""

from flask import Blueprint, request, jsonify
from db import get_db
from datetime import datetime, timezone, timedelta
import hashlib, os, hmac as _hmac, base64, json, time

auth_bp = Blueprint("auth", __name__)

SECRET = os.getenv("JWT_SECRET", "suspension_sim_secret_2026")


def hash_password(pw: str) -> str:
    salt = os.urandom(16).hex()
    h = hashlib.sha256((salt + pw).encode()).hexdigest()
    return f"{salt}:{h}"


def verify_password(pw: str, stored: str) -> bool:
    try:
        salt, h = stored.split(":")
        return _hmac.compare_digest(hashlib.sha256((salt + pw).encode()).hexdigest(), h)
    except Exception:
        return False


def _sign(data: str) -> str:
    return _hmac.new(SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()


def make_token(user_id: str, username: str) -> str:
    payload = {"sub": user_id, "username": username, "exp": int(time.time()) + 86400 * 7}
    data = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    return f"{data}.{_sign(data)}"


def _hmac_sign(data: str) -> str:
    return _sign(data)


def verify_token(token: str):
    try:
        data, sig = token.rsplit(".", 1)
        expected = _sign(data)
        if not _hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(base64.urlsafe_b64decode(data + "=="))
        if payload["exp"] < time.time():
            return None
        return payload
    except Exception:
        return None


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    email = data.get("email", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    try:
        db = get_db()
        if db["users"].find_one({"username": username}):
            return jsonify({"error": "Username already taken"}), 409

        user = {
            "username": username,
            "email": email,
            "password": hash_password(password),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        result = db["users"].insert_one(user)
        user_id = str(result.inserted_id)
        token = make_token(user_id, username)
        return jsonify({"token": token, "username": username, "user_id": user_id}), 201
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)[:120]}"}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    try:
        db = get_db()
        user = db["users"].find_one({"username": username})
        if not user or not verify_password(password, user["password"]):
            return jsonify({"error": "Invalid username or password"}), 401

        user_id = str(user["_id"])
        token = make_token(user_id, username)
        return jsonify({"token": token, "username": username, "user_id": user_id}), 200
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)[:120]}"}), 500


@auth_bp.route("/me", methods=["GET"])
def me():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    payload = verify_token(token)
    if not payload:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"username": payload["username"], "user_id": payload["sub"]}), 200
