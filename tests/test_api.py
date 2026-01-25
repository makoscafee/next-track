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
        """Test recommend with seed tracks (proper format with dicts)."""
        # seed_tracks expects list of dicts with 'name' and 'artist' keys
        response = client.post(
            "/api/v1/recommend",
            json={
                "seed_tracks": [
                    {"name": "Bohemian Rhapsody", "artist": "Queen"},
                    {"name": "Stairway to Heaven", "artist": "Led Zeppelin"},
                ],
                "limit": 5,
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert "recommendations" in data

    def test_recommend_with_mood(self, client):
        """Test recommend with mood parameter."""
        response = client.post("/api/v1/recommend", json={"mood": "happy", "limit": 5})
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"


class TestMoodEndpoint:
    """Tests for mood analysis endpoint."""

    def test_mood_analyze_endpoint_exists(self, client):
        """Test mood analyze endpoint is accessible."""
        response = client.post(
            "/api/v1/mood/analyze", json={"text": "I am feeling great today!"}
        )
        assert response.status_code == 200

    def test_mood_analyze_returns_context(self, client):
        """Test mood analyze returns context detection."""
        response = client.post(
            "/api/v1/mood/analyze",
            json={"text": "Great morning workout in the sunny weather!"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert "mood_analysis" in data
        assert "context" in data["mood_analysis"]

    def test_mood_recommend_endpoint_exists(self, client):
        """Test mood recommend endpoint is accessible."""
        response = client.post(
            "/api/v1/mood/recommend", json={"mood": "happy", "limit": 10}
        )
        assert response.status_code == 200

    def test_mood_recommend_with_context(self, client):
        """Test mood recommend with explicit context."""
        response = client.post(
            "/api/v1/mood/recommend",
            json={
                "mood": "happy",
                "limit": 5,
                "context": {"activity": "workout", "time_of_day": "morning"},
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"


class TestUserEndpoint:
    """Tests for user management endpoints."""

    def test_user_profile_get_requires_user_id(self, client):
        """Test getting user profile requires user_id parameter."""
        # Without user_id, should return 400
        response = client.get("/api/v1/user/profile")
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
        assert "user_id" in data["message"]

    def test_user_history_get_requires_user_id(self, client):
        """Test getting user history requires user_id parameter."""
        # Without user_id, should return 400
        response = client.get("/api/v1/user/history")
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
        assert "user_id" in data["message"]


class TestTrackEndpoint:
    """Tests for track features endpoint."""

    def test_track_features_not_found(self, client):
        """Test getting features for non-existent track returns 404."""
        response = client.get("/api/v1/tracks/nonexistent_track_id_12345/features")
        assert response.status_code == 404
        data = response.get_json()
        assert data["status"] == "error"

    def test_track_search_requires_query(self, client):
        """Test track search requires query parameter."""
        response = client.get("/api/v1/tracks/search")
        assert response.status_code == 400

    def test_track_search_with_query(self, client):
        """Test track search with query parameter."""
        response = client.get("/api/v1/tracks/search?q=queen&limit=5&source=dataset")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert "results" in data
