"""Tests for cold start recommendation strategy."""

from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from app.ml.cold_start import ColdStartRecommender


@pytest.fixture
def sample_tracks_df():
    """Create a sample tracks DataFrame with popularity and genres."""
    np.random.seed(42)
    n = 100
    return pd.DataFrame(
        {
            "id": [f"track_{i}" for i in range(n)],
            "name": [f"Song {i}" for i in range(n)],
            "artists": [
                "Rock Band" if i < 20
                else "Jazz Ensemble" if i < 40
                else "Electronic DJ" if i < 60
                else "Pop Star" if i < 80
                else "Classical Orchestra"
                for i in range(n)
            ],
            "genres": [
                ["rock", "alternative rock"] if i < 20
                else ["jazz", "smooth jazz"] if i < 40
                else ["electronic", "house"] if i < 60
                else ["pop", "dance pop"] if i < 80
                else ["classical", "orchestral"]
                for i in range(n)
            ],
            "popularity": list(range(n, 0, -1)),  # track_0 most popular
            "danceability": np.random.uniform(0, 1, n),
            "energy": np.random.uniform(0, 1, n),
            "valence": np.random.uniform(0, 1, n),
            "tempo": np.random.uniform(0, 1, n),
            "acousticness": np.random.uniform(0, 1, n),
            "instrumentalness": np.random.uniform(0, 1, n),
            "speechiness": np.random.uniform(0, 1, n),
        }
    )


@pytest.fixture
def cold_start(sample_tracks_df):
    """Create an initialized ColdStartRecommender."""
    recommender = ColdStartRecommender()
    recommender.initialize(sample_tracks_df)
    return recommender


@pytest.fixture
def cold_start_with_content(sample_tracks_df):
    """Create a ColdStartRecommender with a fitted content model."""
    from app.ml.content_based import ContentBasedRecommender

    recommender = ColdStartRecommender()
    # Fit a content model
    content_model = ContentBasedRecommender(n_neighbors=10)
    train_df = sample_tracks_df.rename(columns={"id": "track_id"})
    content_model.fit(train_df)

    recommender.initialize(sample_tracks_df, content_model=content_model)
    return recommender


class TestIsColdStart:
    def test_no_user_id(self):
        assert ColdStartRecommender.is_cold_start(None, None) is True

    def test_no_collab_model(self):
        assert ColdStartRecommender.is_cold_start("user_1", None) is True

    def test_unfitted_collab_model(self):
        mock_model = MagicMock()
        mock_model.is_fitted = False
        assert ColdStartRecommender.is_cold_start("user_1", mock_model) is True

    def test_user_not_in_model(self):
        mock_model = MagicMock()
        mock_model.is_fitted = True
        mock_model.user_mapping = {"user_2": 0, "user_3": 1}
        assert ColdStartRecommender.is_cold_start("user_1", mock_model) is True

    def test_known_user(self):
        mock_model = MagicMock()
        mock_model.is_fitted = True
        mock_model.user_mapping = {"user_1": 0, "user_2": 1}
        assert ColdStartRecommender.is_cold_start("user_1", mock_model) is False


class TestRecommendPopular:
    def test_returns_tracks(self, cold_start):
        recs = cold_start.recommend_popular(n=5)
        assert len(recs) == 5

    def test_sorted_by_score(self, cold_start):
        recs = cold_start.recommend_popular(n=10)
        scores = [r["score"] for r in recs]
        assert scores == sorted(scores, reverse=True)

    def test_scores_normalized(self, cold_start):
        recs = cold_start.recommend_popular(n=5)
        assert all(0 <= r["score"] <= 1 for r in recs)
        assert recs[0]["score"] == 1.0  # Top track normalized to 1.0

    def test_source_tag(self, cold_start):
        recs = cold_start.recommend_popular(n=3)
        assert all(r["source"] == "cold_start_popular" for r in recs)

    def test_exclude_tracks(self, cold_start):
        recs = cold_start.recommend_popular(n=5, exclude_tracks=["track_0"])
        ids = [r["track_id"] for r in recs]
        assert "track_0" not in ids

    def test_uninitialized(self):
        recommender = ColdStartRecommender()
        recs = recommender.recommend_popular(n=5)
        assert recs == []


class TestRecommendForGenres:
    def test_returns_matching_tracks(self, cold_start):
        recs = cold_start.recommend_for_genres(["rock"], n=5)
        assert len(recs) > 0
        assert all(r["source"] == "cold_start_genre" for r in recs)

    def test_multiple_genres(self, cold_start):
        recs = cold_start.recommend_for_genres(["rock", "jazz"], n=10)
        assert len(recs) > 0

    def test_no_match(self, cold_start):
        recs = cold_start.recommend_for_genres(["nonexistent_genre_xyz"], n=5)
        assert len(recs) == 0

    def test_empty_genres(self, cold_start):
        recs = cold_start.recommend_for_genres([], n=5)
        assert recs == []

    def test_exclude_tracks(self, cold_start):
        recs = cold_start.recommend_for_genres(
            ["rock"], n=5, exclude_tracks=["track_0"]
        )
        ids = [r["track_id"] for r in recs]
        assert "track_0" not in ids

    def test_ranked_by_popularity(self, cold_start):
        recs = cold_start.recommend_for_genres(["rock"], n=5)
        scores = [r["score"] for r in recs]
        assert scores == sorted(scores, reverse=True)

    def test_matches_genre_metadata_not_names(self, cold_start):
        """Verify genre filtering uses actual genre column, not artist names."""
        # "electronic" is in genres for tracks 40-59 but not in artist name "Electronic DJ"
        # for exact genre matching. "house" is only in genres, never in names/artists.
        recs = cold_start.recommend_for_genres(["house"], n=10)
        assert len(recs) > 0
        # All returned tracks should be from the electronic group (tracks 40-59)
        for r in recs:
            idx = int(r["track_id"].split("_")[1])
            assert 40 <= idx < 60, f"track_{idx} should be in electronic genre group"

    def test_partial_genre_match(self, cold_start):
        """Verify partial matching works (e.g. 'alternative' matches 'alternative rock')."""
        recs = cold_start.recommend_for_genres(["alternative"], n=5)
        assert len(recs) > 0
        # Should match tracks 0-19 which have "alternative rock" genre
        for r in recs:
            idx = int(r["track_id"].split("_")[1])
            assert idx < 20


class TestRecommendForPreferences:
    def test_returns_tracks(self, cold_start_with_content):
        prefs = {"preferred_valence": 0.8, "preferred_energy": 0.7}
        recs = cold_start_with_content.recommend_for_preferences(prefs, n=5)
        assert len(recs) == 5
        assert all(r["source"] == "cold_start_preferences" for r in recs)

    def test_energy_preference_label(self, cold_start_with_content):
        prefs = {"energy_preference": "high"}
        recs = cold_start_with_content.recommend_for_preferences(prefs, n=5)
        assert len(recs) == 5

    def test_mood_preference_label(self, cold_start_with_content):
        prefs = {"mood_preference": "happy"}
        recs = cold_start_with_content.recommend_for_preferences(prefs, n=5)
        assert len(recs) == 5

    def test_no_content_model(self, cold_start):
        prefs = {"preferred_valence": 0.8}
        recs = cold_start.recommend_for_preferences(prefs, n=5)
        assert recs == []

    def test_exclude_tracks(self, cold_start_with_content):
        prefs = {"preferred_energy": 0.5}
        recs = cold_start_with_content.recommend_for_preferences(
            prefs, n=5, exclude_tracks=["track_0"]
        )
        ids = [r["track_id"] for r in recs]
        assert "track_0" not in ids


class TestGetColdStartRecommendations:
    def test_genre_strategy_priority(self, cold_start):
        recs, strategy = cold_start.get_cold_start_recommendations(
            preferred_genres=["rock"], n=5
        )
        assert strategy == "genre"
        assert len(recs) > 0

    def test_preference_strategy(self, cold_start_with_content):
        recs, strategy = cold_start_with_content.get_cold_start_recommendations(
            preferences={"preferred_energy": 0.8}, n=5
        )
        assert strategy == "preferences"
        assert len(recs) > 0

    def test_popularity_fallback(self, cold_start):
        recs, strategy = cold_start.get_cold_start_recommendations(n=5)
        assert strategy == "popular"
        assert len(recs) == 5

    def test_genre_priority_over_preferences(self, cold_start_with_content):
        recs, strategy = cold_start_with_content.get_cold_start_recommendations(
            preferred_genres=["rock"],
            preferences={"preferred_energy": 0.8},
            n=5,
        )
        assert strategy == "genre"

    def test_uninitialized(self):
        recommender = ColdStartRecommender()
        recs, strategy = recommender.get_cold_start_recommendations(n=5)
        assert strategy == "uninitialized"
        assert recs == []

    def test_genre_miss_falls_to_popularity(self, cold_start):
        """If genre search returns nothing, fall through to popularity."""
        recs, strategy = cold_start.get_cold_start_recommendations(
            preferred_genres=["nonexistent_xyz"], n=5
        )
        assert strategy == "popular"
        assert len(recs) == 5
