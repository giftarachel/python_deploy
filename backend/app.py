"""
Matrix-Based Force Distribution in a Multi-Link Suspension System
Flask Backend
"""

from flask import Flask
from flask_cors import CORS
from routes.simulate import simulate_bp
from routes.history import history_bp
from routes.pdf import pdf_bp
from routes.chat import chat_bp
from routes.auth import auth_bp
from db import init_db

app = Flask(__name__)
CORS(app)

init_db()

app.register_blueprint(simulate_bp, url_prefix="/api")
app.register_blueprint(history_bp, url_prefix="/api")
app.register_blueprint(pdf_bp, url_prefix="/api")
app.register_blueprint(chat_bp, url_prefix="/api")
app.register_blueprint(auth_bp, url_prefix="/api")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") != "production"
    app.run(debug=debug, host="0.0.0.0", port=port)
