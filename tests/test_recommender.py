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

    def test_initialization_with_algorithm(self):
        """Test recommender initializes with custom algorithm."""
        recommender = ContentBasedRecommender(n_neighbors=20, algorithm="brute")
        assert recommender.n_neighbors == 20
        assert recommender.algorithm == "brute"

    def test_fit(self, sample_tracks_df):
        """Test fitting the model."""
        recommender = ContentBasedRecommender()
        recommender.fit(sample_tracks_df)
        assert recommender.is_fitted
        assert len(recommender.track_ids) == 100
        assert len(recommender._track_id_to_idx) == 100

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

    def test_recommend_with_array_input(self, sample_tracks_df):
        """Test recommendations with array input instead of dict."""
        recommender = ContentBasedRecommender()
        recommender.fit(sample_tracks_df)

        seed_features = [0.7, 0.8, 0.6, 120, 0.2, 0.1, 0.05]
        recommendations = recommender.recommend(seed_features, n_recommendations=5)
        assert len(recommendations) == 5

    def test_recommend_from_track_id(self, sample_tracks_df):
        """Test getting recommendations from track ID."""
        recommender = ContentBasedRecommender()
        recommender.fit(sample_tracks_df)

        recommendations = recommender.recommend_from_track_id(
            "track_0", n_recommendations=5
        )
        assert len(recommendations) == 5
        assert "track_0" not in [rec["track_id"] for rec in recommendations]

    def test_recommend_from_invalid_track_id(self, sample_tracks_df):
        """Test recommendations for non-existent track ID."""
        recommender = ContentBasedRecommender()
        recommender.fit(sample_tracks_df)

        recommendations = recommender.recommend_from_track_id(
            "invalid_track", n_recommendations=5
        )
        assert recommendations == []

    def test_recommend_batch(self, sample_tracks_df):
        """Test batch recommendations."""
        recommender = ContentBasedRecommender()
        recommender.fit(sample_tracks_df)

        seed_features_list = [
            {
                "danceability": 0.7,
                "energy": 0.8,
                "valence": 0.6,
                "tempo": 120,
                "acousticness": 0.2,
                "instrumentalness": 0.1,
                "speechiness": 0.05,
            },
            {
                "danceability": 0.3,
                "energy": 0.2,
                "valence": 0.4,
                "tempo": 80,
                "acousticness": 0.8,
                "instrumentalness": 0.6,
                "speechiness": 0.1,
            },
        ]

        batch_results = recommender.recommend_batch(
            seed_features_list, n_recommendations=5
        )
        assert len(batch_results) == 2
        assert all(len(recs) == 5 for recs in batch_results)

    def test_recommend_from_track_ids_batch(self, sample_tracks_df):
        """Test batch recommendations from track IDs."""
        recommender = ContentBasedRecommender()
        recommender.fit(sample_tracks_df)

        track_ids = ["track_0", "track_10", "track_50"]
        batch_results = recommender.recommend_from_track_ids_batch(
            track_ids, n_recommendations=5
        )

        assert len(batch_results) == 3
        assert all(len(recs) == 5 for recs in batch_results)
        # Ensure seed tracks are not in their own recommendations
        for i, track_id in enumerate(track_ids):
            assert track_id not in [rec["track_id"] for rec in batch_results[i]]

    def test_recommend_from_track_ids_batch_with_invalid(self, sample_tracks_df):
        """Test batch recommendations with some invalid track IDs."""
        recommender = ContentBasedRecommender()
        recommender.fit(sample_tracks_df)

        track_ids = ["track_0", "invalid_track", "track_50"]
        batch_results = recommender.recommend_from_track_ids_batch(
            track_ids, n_recommendations=5
        )

        assert len(batch_results) == 3
        assert len(batch_results[0]) == 5  # Valid
        assert len(batch_results[1]) == 0  # Invalid
        assert len(batch_results[2]) == 5  # Valid

    def test_get_track_features(self, sample_tracks_df):
        """Test retrieving track features."""
        recommender = ContentBasedRecommender()
        recommender.fit(sample_tracks_df)

        features = recommender.get_track_features("track_0")
        assert features is not None
        assert "danceability" in features
        assert "energy" in features
        assert all(isinstance(v, float) for v in features.values())

    def test_get_track_features_invalid(self, sample_tracks_df):
        """Test retrieving features for invalid track."""
        recommender = ContentBasedRecommender()
        recommender.fit(sample_tracks_df)

        features = recommender.get_track_features("invalid_track")
        assert features is None

    def test_similarity_scores_sorted(self, sample_tracks_df):
        """Test that similarity scores are sorted descending."""
        recommender = ContentBasedRecommender()
        recommender.fit(sample_tracks_df)

        seed_features = {f: 0.5 for f in ContentBasedRecommender.FEATURES}
        recommendations = recommender.recommend(seed_features, n_recommendations=10)

        scores = [rec["similarity_score"] for rec in recommendations]
        assert scores == sorted(scores, reverse=True)

    def test_similarity_scores_in_range(self, sample_tracks_df):
        """Test that similarity scores are between 0 and 1."""
        recommender = ContentBasedRecommender()
        recommender.fit(sample_tracks_df)

        seed_features = {f: 0.5 for f in ContentBasedRecommender.FEATURES}
        recommendations = recommender.recommend(seed_features, n_recommendations=10)

        for rec in recommendations:
            assert 0 <= rec["similarity_score"] <= 1

    def test_recommend_unfitted(self):
        """Test that unfitted model returns empty list."""
        recommender = ContentBasedRecommender()
        seed_features = {f: 0.5 for f in ContentBasedRecommender.FEATURES}
        recommendations = recommender.recommend(seed_features, n_recommendations=5)
        assert recommendations == []

    def test_recommend_from_track_id_unfitted(self):
        """Test that unfitted model returns empty list for track ID."""
        recommender = ContentBasedRecommender()
        recommendations = recommender.recommend_from_track_id(
            "track_0", n_recommendations=5
        )
        assert recommendations == []


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

        # High valence, high energy should be in Q1 (happy/excited/joy)
        emotion = recommender.get_emotion_for_features(0.8, 0.8)
        assert emotion in [
            "happy",
            "excited",
            "energetic",
            "joy",
            "elated",
            "enthusiastic",
        ]

        # Low valence, low energy should be in Q3 (sad/depressed/melancholic)
        emotion = recommender.get_emotion_for_features(0.2, 0.2)
        assert emotion in [
            "sad",
            "sadness",
            "depressed",
            "melancholic",
            "bored",
            "lonely",
        ]

        # High valence, low energy should be in Q4 (calm/relaxed/peaceful)
        emotion = recommender.get_emotion_for_features(0.65, 0.2)
        assert emotion in ["calm", "relaxed", "peaceful", "serene", "content"]

        # Low valence, high energy should be in Q2 (angry/anxious/fear)
        emotion = recommender.get_emotion_for_features(0.2, 0.85)
        assert emotion in [
            "angry",
            "anger",
            "anxious",
            "fear",
            "stressed",
            "frustrated",
            "tense",
        ]


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
