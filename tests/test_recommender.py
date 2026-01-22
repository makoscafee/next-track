"""
Tests for recommendation models
"""

import numpy as np
import pandas as pd
import pytest

from app.ml.content_based import ContentBasedRecommender
from app.ml.hybrid import HybridRecommender
from app.ml.sentiment_aware import SentimentAwareRecommender


@pytest.fixture
def sample_tracks_df():
    """Create sample track features dataframe."""
    np.random.seed(42)
    n_tracks = 100

    return pd.DataFrame(
        {
            "track_id": [f"track_{i}" for i in range(n_tracks)],
            "danceability": np.random.uniform(0, 1, n_tracks),
            "energy": np.random.uniform(0, 1, n_tracks),
            "valence": np.random.uniform(0, 1, n_tracks),
            "tempo": np.random.uniform(60, 180, n_tracks),
            "acousticness": np.random.uniform(0, 1, n_tracks),
            "instrumentalness": np.random.uniform(0, 1, n_tracks),
            "speechiness": np.random.uniform(0, 1, n_tracks),
        }
    )


class TestContentBasedRecommender:
    """Tests for content-based recommender."""

    def test_initialization(self):
        """Test recommender initializes correctly."""
        recommender = ContentBasedRecommender(n_neighbors=10)
        assert recommender.n_neighbors == 10
        assert not recommender.is_fitted

    def test_fit(self, sample_tracks_df):
        """Test fitting the model."""
        recommender = ContentBasedRecommender()
        recommender.fit(sample_tracks_df)
        assert recommender.is_fitted
        assert len(recommender.track_ids) == 100

    def test_recommend(self, sample_tracks_df):
        """Test getting recommendations."""
        recommender = ContentBasedRecommender()
        recommender.fit(sample_tracks_df)

        seed_features = {
            "danceability": 0.7,
            "energy": 0.8,
            "valence": 0.6,
            "tempo": 120,
            "acousticness": 0.2,
            "instrumentalness": 0.1,
            "speechiness": 0.05,
        }

        recommendations = recommender.recommend(seed_features, n_recommendations=5)
        assert len(recommendations) == 5
        assert all("track_id" in rec for rec in recommendations)
        assert all("similarity_score" in rec for rec in recommendations)

    def test_recommend_from_track_id(self, sample_tracks_df):
        """Test getting recommendations from track ID."""
        recommender = ContentBasedRecommender()
        recommender.fit(sample_tracks_df)

        recommendations = recommender.recommend_from_track_id(
            "track_0", n_recommendations=5
        )
        assert len(recommendations) == 5
        assert "track_0" not in [rec["track_id"] for rec in recommendations]


class TestSentimentAwareRecommender:
    """Tests for sentiment-aware recommender."""

    def test_emotion_mapping(self):
        """Test emotion to valence-energy mapping exists."""
        recommender = SentimentAwareRecommender()
        assert "happy" in recommender.EMOTION_MAP
        assert "sad" in recommender.EMOTION_MAP

        valence, energy = recommender.EMOTION_MAP["happy"]
        assert 0 <= valence <= 1
        assert 0 <= energy <= 1

    def test_recommend_for_mood(self, sample_tracks_df):
        """Test mood-based recommendations."""
        recommender = SentimentAwareRecommender()
        recommender.fit(sample_tracks_df)

        recommendations = recommender.recommend_for_mood("happy", n_recommendations=5)
        assert len(recommendations) == 5
        assert all("mood_score" in rec for rec in recommendations)

    def test_get_emotion_for_features(self):
        """Test determining emotion from features."""
        recommender = SentimentAwareRecommender()

        # High valence, high energy should be happy/excited
        emotion = recommender.get_emotion_for_features(0.8, 0.8)
        assert emotion in ["happy", "excited", "energetic"]

        # Low valence, low energy should be sad
        emotion = recommender.get_emotion_for_features(0.2, 0.2)
        assert emotion in ["sad", "peaceful", "relaxed"]


class TestHybridRecommender:
    """Tests for hybrid recommender."""

    def test_initialization(self):
        """Test hybrid recommender initializes with correct weights."""
        recommender = HybridRecommender(
            content_weight=0.4, collab_weight=0.35, sentiment_weight=0.25
        )
        assert recommender.weights["content"] == 0.4
        assert recommender.weights["collaborative"] == 0.35
        assert recommender.weights["sentiment"] == 0.25

    def test_update_weights(self):
        """Test updating weights."""
        recommender = HybridRecommender()
        recommender.update_weights(content=0.5, collaborative=0.3, sentiment=0.2)

        assert recommender.weights["content"] == 0.5
        assert recommender.weights["collaborative"] == 0.3
        assert recommender.weights["sentiment"] == 0.2

    def test_content_only_recommend(self, sample_tracks_df):
        """Test recommendations with only content-based model."""
        recommender = HybridRecommender()
        recommender.fit_content(sample_tracks_df)

        seed_features = {
            "danceability": 0.7,
            "energy": 0.8,
            "valence": 0.6,
            "tempo": 120,
            "acousticness": 0.2,
            "instrumentalness": 0.1,
            "speechiness": 0.05,
        }

        recommendations = recommender.recommend(
            seed_track_features=seed_features, n_recommendations=5
        )
        assert len(recommendations) <= 5
