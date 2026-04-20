"""
POST /api/chat  - AI Engineering Chatbot powered by Groq (LLaMA 3).
Specialized in suspension mechanics, matrix math, and force distribution.
"""

from flask import Blueprint, request, jsonify
from groq import Groq
import os

chat_bp = Blueprint("chat", __name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

SYSTEM_PROMPT = """You are an expert mechanical engineering assistant specializing in:
- Multi-link vehicle suspension systems
- Matrix-based force distribution and static equilibrium
- Direction Cosine Matrix (DCM) construction and interpretation
- Linear algebra: matrix inversion, least-squares solvers
- Force propagation through suspension topologies
- Bump, braking, and cornering load cases

Answer concisely and technically. When relevant, reference the equation A·T = F where:
  A = Direction Cosine Matrix, T = link force vector, F = external force vector.
If asked about simulation results, help interpret the force distribution data."""


@chat_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    context = data.get("context", "")

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    if not GROQ_API_KEY:
        return jsonify({"error": "AI chatbot is not configured. Please set GROQ_API_KEY in environment variables."}), 503

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if context:
        messages.append({
            "role": "system",
            "content": f"Current simulation context:\n{context}"
        })

    messages.append({"role": "user", "content": user_message})

    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=512,
            temperature=0.4,
        )
        reply = response.choices[0].message.content
        return jsonify({"reply": reply}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
