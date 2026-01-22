"""
Tests for API endpoints
"""

import pytest
from app import create_app


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app("testing")
    yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health endpoint returns success."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["service"] == "nexttrack"


class TestRecommendEndpoint:
    """Tests for recommendation endpoint."""

    def test_recommend_endpoint_exists(self, client):
        """Test recommend endpoint is accessible."""
        response = client.post("/api/v1/recommend", json={})
        assert response.status_code == 200

    def test_recommend_with_seed_tracks(self, client):
        """Test recommend with seed tracks."""
        response = client.post(
            "/api/v1/recommend", json={"seed_tracks": ["track1", "track2"], "limit": 5}
        )
        assert response.status_code == 200


class TestMoodEndpoint:
    """Tests for mood analysis endpoint."""

    def test_mood_analyze_endpoint_exists(self, client):
        """Test mood analyze endpoint is accessible."""
        response = client.post(
            "/api/v1/mood/analyze", json={"text": "I am feeling great today!"}
        )
        assert response.status_code == 200

    def test_mood_recommend_endpoint_exists(self, client):
        """Test mood recommend endpoint is accessible."""
        response = client.post(
            "/api/v1/mood/recommend", json={"mood": "happy", "limit": 10}
        )
        assert response.status_code == 200


class TestUserEndpoint:
    """Tests for user management endpoints."""

    def test_user_profile_get(self, client):
        """Test getting user profile."""
        response = client.get("/api/v1/user/profile")
        assert response.status_code == 200

    def test_user_history_get(self, client):
        """Test getting user history."""
        response = client.get("/api/v1/user/history")
        assert response.status_code == 200


class TestTrackEndpoint:
    """Tests for track features endpoint."""

    def test_track_features_endpoint(self, client):
        """Test getting track features."""
        response = client.get("/api/v1/tracks/test_track_id/features")
        response = client.get('/api/v1/tracks/test_track_id/features')
        assert response.status_code == 200
