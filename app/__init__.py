"""
NextTrack - Music Recommendation API
Flask application factory
"""
from flask import Flask
from flask_cors import CORS

from app.config import config
from app.extensions import db, migrate, jwt, cache


def create_app(config_name='development'):
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
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')

    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'nexttrack'}

    return app
