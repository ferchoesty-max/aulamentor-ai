import os
from flask import Flask
from flask_cors import CORS
from src.core.errors import register_error_handlers
from src.auth.security import authenticate_request
from src.firebase.client import ensure_firebase
from src.http.routes_health import health_bp
from src.http.routes_auth import auth_bp

def create_app(testing: bool = False) -> Flask:
    app = Flask(__name__)
    app.config.update(
        TESTING=testing,
        MAX_CONTENT_LENGTH=256 * 1024
    )
    register_error_handlers(app)

    allowed = [o.strip() for o in os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',') if o.strip()]
    CORS(app, origins=allowed, allow_headers=['Authorization', 'Content-Type'], methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])

    if not testing:
        ensure_firebase()

    app.before_request(authenticate_request)

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)

    return app
