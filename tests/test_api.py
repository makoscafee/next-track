"""
Tests for API endpoints
"""

from unittest.mock import patch

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


class TestTrackSearchPagination:
    """Tests for pagination and filtering on the track search endpoint."""

    # Sample tracks for mocking: 8 tracks, 2 explicit
    MOCK_TRACKS = [
        {"id": f"t{i}", "name": f"Track {i}", "artists": "Artist", "explicit": i % 4 == 0}
        for i in range(8)
    ]

    def _mock_search(self, tracks):
        """Return a side_effect fn for dataset_service.search_tracks."""

        def _search(query, limit=10, offset=0, exclude_explicit=False):
            filtered = [
                t for t in tracks
                if not (exclude_explicit and t.get("explicit"))
            ]
            total = len(filtered)
            return filtered[offset: offset + limit], total

        return _search

    def test_search_metadata_includes_pagination_fields(self, client):
        """Response metadata includes total, offset, limit, has_more."""
        with patch(
            "app.api.v1.tracks.dataset_service.search_tracks",
            side_effect=self._mock_search(self.MOCK_TRACKS),
        ), patch("app.api.v1.tracks.dataset_service.load_dataset"):
            response = client.get(
                "/api/v1/tracks/search?q=track&limit=5&offset=0&source=dataset"
            )
        assert response.status_code == 200
        meta = response.get_json()["metadata"]
        assert "total" in meta
        assert "offset" in meta
        assert "limit" in meta
        assert "has_more" in meta
        assert meta["offset"] == 0
        assert meta["limit"] == 5

    def test_search_with_offset_skips_results(self, client):
        """Offset parameter skips the expected number of results."""
        with patch(
            "app.api.v1.tracks.dataset_service.search_tracks",
            side_effect=self._mock_search(self.MOCK_TRACKS),
        ), patch("app.api.v1.tracks.dataset_service.load_dataset"):
            r0 = client.get(
                "/api/v1/tracks/search?q=track&limit=3&offset=0&source=dataset"
            ).get_json()
            r1 = client.get(
                "/api/v1/tracks/search?q=track&limit=3&offset=3&source=dataset"
            ).get_json()

        ids_page0 = [t["track_id"] for t in r0["results"]]
        ids_page1 = [t["track_id"] for t in r1["results"]]
        assert ids_page0 != ids_page1
        assert not set(ids_page0) & set(ids_page1), "Pages should not overlap"

    def test_search_has_more_true_when_more_results_exist(self, client):
        """has_more is True when offset+count < total."""
        with patch(
            "app.api.v1.tracks.dataset_service.search_tracks",
            side_effect=self._mock_search(self.MOCK_TRACKS),
        ), patch("app.api.v1.tracks.dataset_service.load_dataset"):
            response = client.get(
                "/api/v1/tracks/search?q=track&limit=3&offset=0&source=dataset"
            )
        meta = response.get_json()["metadata"]
        assert meta["has_more"] is True

    def test_search_has_more_false_on_last_page(self, client):
        """has_more is False on the final page of results."""
        with patch(
            "app.api.v1.tracks.dataset_service.search_tracks",
            side_effect=self._mock_search(self.MOCK_TRACKS),
        ), patch("app.api.v1.tracks.dataset_service.load_dataset"):
            response = client.get(
                "/api/v1/tracks/search?q=track&limit=5&offset=5&source=dataset"
            )
        meta = response.get_json()["metadata"]
        assert meta["has_more"] is False

    def test_search_exclude_explicit_filters_tracks(self, client):
        """exclude_explicit=true removes explicit tracks from results."""
        with patch(
            "app.api.v1.tracks.dataset_service.search_tracks",
            side_effect=self._mock_search(self.MOCK_TRACKS),
        ), patch("app.api.v1.tracks.dataset_service.load_dataset"):
            response = client.get(
                "/api/v1/tracks/search?q=track&limit=10&exclude_explicit=true&source=dataset"
            )
        data = response.get_json()
        assert response.status_code == 200
        for track in data["results"]:
            assert not track.get("explicit"), f"Explicit track leaked: {track}"

    def test_search_explicit_included_by_default(self, client):
        """Without exclude_explicit, explicit tracks appear in results."""
        with patch(
            "app.api.v1.tracks.dataset_service.search_tracks",
            side_effect=self._mock_search(self.MOCK_TRACKS),
        ), patch("app.api.v1.tracks.dataset_service.load_dataset"):
            response = client.get(
                "/api/v1/tracks/search?q=track&limit=10&source=dataset"
            )
        data = response.get_json()
        explicit_flags = [t.get("explicit") for t in data["results"]]
        assert any(explicit_flags), "Expected at least one explicit track in unfiltered results"


class TestRecommendExplicitFilter:
    """Tests for exclude_explicit on the recommend endpoint."""

    def test_recommend_exclude_explicit_accepted(self, client):
        """exclude_explicit field is accepted without error."""
        response = client.post(
            "/api/v1/recommend",
            json={"exclude_explicit": True, "limit": 5},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"

    def test_recommend_exclude_explicit_filters_results(self, client):
        """Explicit tracks are removed from recommendations when flag is set."""
        explicit_rec = {
            "name": "Explicit Song",
            "artist": "Rude Artist",
            "track_id": "explicit_001",
            "score": 0.9,
            "source": "hybrid",
            "explicit": True,
            "audio_features": {"explicit": True},
        }
        clean_rec = {
            "name": "Clean Song",
            "artist": "Nice Artist",
            "track_id": "clean_001",
            "score": 0.8,
            "source": "hybrid",
            "explicit": False,
            "audio_features": {"explicit": False},
        }

        with patch(
            "app.services.recommendation.RecommendationService.get_recommendations",
            return_value=[clean_rec],
        ):
            response = client.post(
                "/api/v1/recommend",
                json={"exclude_explicit": True, "limit": 5},
            )

        data = response.get_json()
        assert response.status_code == 200
        track_ids = [r.get("track_id") for r in data["recommendations"]]
        assert "explicit_001" not in track_ids
