"""
Configuration settings for NextTrack API
"""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT Settings
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour

    # Last.fm API
    LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
    LASTFM_API_SECRET = os.getenv("LASTFM_API_SECRET")

    # Dataset paths
    DATASET_PATH = os.getenv("DATASET_PATH", "data/processed/tracks.csv")

    # Cache settings
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "postgresql://localhost/nexttrack_dev"
    )


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    # Use SQLite in-memory for tests (no external DB required)
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    CACHE_TYPE = "redis"
    CACHE_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
