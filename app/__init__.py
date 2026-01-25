"""
NextTrack - Music Recommendation API
Flask application factory
"""

from flask import Flask
from flask_cors import CORS

from app.config import config
from app.extensions import cache, db, jwt, migrate


def create_app(config_name="development"):
    """Application factory pattern."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cache.init_app(app)
    CORS(app)

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
