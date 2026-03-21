"""
NextTrack - Music Recommendation API
Flask application factory
"""

import os

from flasgger import Swagger
from flask import Flask
from flask_cors import CORS

from app.config import config
from app.extensions import cache, db, jwt, migrate

SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/api/v1/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs/",
}

SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "NextTrack API",
        "description": (
            "Emotionally-aware hybrid music recommendation API. "
            "Combines content-based K-NN filtering, ALS collaborative filtering, "
            "and sentiment-aware mood analysis into a single configurable pipeline."
        ),
        "version": "1.0.0",
        "contact": {"email": "admin@nexttrack.example.com"},
    },
    "basePath": "/api/v1",
    "schemes": ["http", "https"],
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT token. Format: **Bearer &lt;token&gt;**",
        }
    },
    "tags": [
        {"name": "Recommendations", "description": "Hybrid recommendation endpoints"},
        {"name": "Mood", "description": "Mood analysis and mood-driven recommendations"},
        {"name": "Tracks", "description": "Track search, info, and audio features"},
        {"name": "User", "description": "User profiles and listening history"},
        {"name": "Experiments", "description": "A/B testing and feedback"},
        {"name": "Auth", "description": "Admin authentication"},
        {"name": "Admin", "description": "Protected admin dashboard endpoints"},
    ],
}


def create_app(config_name="development"):
    """Application factory pattern."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cache.init_app(app)
    Swagger(app, config=SWAGGER_CONFIG, template=SWAGGER_TEMPLATE)

    # Configure CORS
    frontend_origins = os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173",
    )
    CORS(
        app,
        origins=frontend_origins.split(","),
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    # Register blueprints
    from app.api.v1 import api_v1_bp

    app.register_blueprint(api_v1_bp, url_prefix="/api/v1")

    # Initialize ML models
    with app.app_context():
        from app.ml.cached_recommender import init_all_recommenders

        init_all_recommenders(app)

    # Health check endpoint
    @app.route("/health")
    def health_check():
        from app.ml.cached_recommender import (
            get_cached_cf_recommender,
            get_cached_recommender,
        )

        content_rec = get_cached_recommender()
        cf_rec = get_cached_cf_recommender()
        return {
            "status": "healthy",
            "service": "nexttrack",
            "models": {
                "content_based": content_rec.model_info,
                "collaborative": cf_rec.model_info,
            },
        }

    return app
