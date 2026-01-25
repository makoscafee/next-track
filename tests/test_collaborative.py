"""
Tests for collaborative filtering models
"""

import numpy as np
import pytest
from scipy import sparse

from app.ml.collaborative import CollaborativeFilteringRecommender


@pytest.fixture
def sample_interaction_matrix():
    """Create sample user-item interaction matrix."""
    np.random.seed(42)
    n_users = 50
    n_tracks = 100

    # Create sparse matrix with ~5% density
    rows = []
    cols = []
    data = []

    for user_idx in range(n_users):
        # Each user interacts with 5-15 tracks
        n_interactions = np.random.randint(5, 15)
        track_indices = np.random.choice(n_tracks, size=n_interactions, replace=False)

        for track_idx in track_indices:
            rows.append(user_idx)
            cols.append(track_idx)
            data.append(np.random.uniform(1, 10))  # Random play count

    matrix = sparse.csr_matrix((data, (rows, cols)), shape=(n_users, n_tracks))
    return matrix


@pytest.fixture
def sample_user_ids():
    """Create sample user IDs."""
    return [f"user_{i}" for i in range(50)]


@pytest.fixture
def sample_track_ids():
    """Create sample track IDs."""
    return [f"track_{i}" for i in range(100)]


class TestCollaborativeFilteringRecommender:
    """Tests for collaborative filtering recommender."""

    def test_initialization(self):
        """Test recommender initializes correctly."""
        recommender = CollaborativeFilteringRecommender(
            n_factors=20,
            regularization=0.05,
            iterations=30,
        )
        assert recommender.n_factors == 20
        assert recommender.regularization == 0.05
        assert recommender.iterations == 30
        assert not recommender.is_fitted

    def test_fit(self, sample_interaction_matrix, sample_user_ids, sample_track_ids):
        """Test fitting the model."""
        recommender = CollaborativeFilteringRecommender(
            n_factors=10,
            iterations=10,
        )
        recommender.fit(sample_interaction_matrix, sample_user_ids, sample_track_ids)

        assert recommender.is_fitted
        assert len(recommender.user_mapping) == 50
        assert len(recommender.track_mapping) == 100

    def test_recommend_for_user(
        self, sample_interaction_matrix, sample_user_ids, sample_track_ids
    ):
        """Test getting recommendations for a user."""
        recommender = CollaborativeFilteringRecommender(
            n_factors=10,
            iterations=10,
        )
        recommender.fit(sample_interaction_matrix, sample_user_ids, sample_track_ids)

        recommendations = recommender.recommend_for_user("user_0", n_recommendations=5)

        assert len(recommendations) == 5
        assert all("track_id" in rec for rec in recommendations)
        assert all("cf_score" in rec for rec in recommendations)

    def test_recommend_for_invalid_user(
        self, sample_interaction_matrix, sample_user_ids, sample_track_ids
    ):
        """Test recommendations for non-existent user."""
        recommender = CollaborativeFilteringRecommender(
            n_factors=10,
            iterations=10,
        )
        recommender.fit(sample_interaction_matrix, sample_user_ids, sample_track_ids)

        recommendations = recommender.recommend_for_user(
            "invalid_user", n_recommendations=5
        )
        assert recommendations == []

    def test_get_similar_users(
        self, sample_interaction_matrix, sample_user_ids, sample_track_ids
    ):
        """Test finding similar users."""
        recommender = CollaborativeFilteringRecommender(
            n_factors=10,
            iterations=10,
        )
        recommender.fit(sample_interaction_matrix, sample_user_ids, sample_track_ids)

        similar = recommender.get_similar_users("user_0", n_users=5)

        assert len(similar) == 5
        assert all("user_id" in s for s in similar)
        assert all("similarity" in s for s in similar)
        # Should not include the user themselves
        assert "user_0" not in [s["user_id"] for s in similar]

    def test_get_similar_users_invalid(
        self, sample_interaction_matrix, sample_user_ids, sample_track_ids
    ):
        """Test similar users for non-existent user."""
        recommender = CollaborativeFilteringRecommender(
            n_factors=10,
            iterations=10,
        )
        recommender.fit(sample_interaction_matrix, sample_user_ids, sample_track_ids)

        similar = recommender.get_similar_users("invalid_user", n_users=5)
        assert similar == []

    def test_cf_scores_positive(
        self, sample_interaction_matrix, sample_user_ids, sample_track_ids
    ):
        """Test that CF scores are non-negative."""
        recommender = CollaborativeFilteringRecommender(
            n_factors=10,
            iterations=10,
        )
        recommender.fit(sample_interaction_matrix, sample_user_ids, sample_track_ids)

        recommendations = recommender.recommend_for_user("user_0", n_recommendations=10)

        for rec in recommendations:
            assert rec["cf_score"] >= 0

    def test_cf_scores_sorted(
        self, sample_interaction_matrix, sample_user_ids, sample_track_ids
    ):
        """Test that CF scores are sorted descending."""
        recommender = CollaborativeFilteringRecommender(
            n_factors=10,
            iterations=10,
        )
        recommender.fit(sample_interaction_matrix, sample_user_ids, sample_track_ids)

        recommendations = recommender.recommend_for_user("user_0", n_recommendations=10)
        scores = [rec["cf_score"] for rec in recommendations]

        assert scores == sorted(scores, reverse=True)

    def test_recommend_unfitted(self):
        """Test that unfitted model returns empty list."""
        recommender = CollaborativeFilteringRecommender()
        recommendations = recommender.recommend_for_user("user_0", n_recommendations=5)
        assert recommendations == []

    def test_similar_users_unfitted(self):
        """Test that unfitted model returns empty list for similar users."""
        recommender = CollaborativeFilteringRecommender()
        similar = recommender.get_similar_users("user_0", n_users=5)
        assert similar == []

    def test_filter_already_liked(
        self, sample_interaction_matrix, sample_user_ids, sample_track_ids
    ):
        """Test that already liked items can be filtered."""
        recommender = CollaborativeFilteringRecommender(
            n_factors=10,
            iterations=10,
        )
        recommender.fit(sample_interaction_matrix, sample_user_ids, sample_track_ids)

        # Get user's interacted tracks
        user_idx = recommender.user_mapping["user_0"]
        interacted_track_indices = sample_interaction_matrix[user_idx].nonzero()[1]
        interacted_tracks = {sample_track_ids[i] for i in interacted_track_indices}

        # Get recommendations with filter
        recommendations = recommender.recommend_for_user(
            "user_0", n_recommendations=10, filter_already_liked=True
        )

        recommended_tracks = {rec["track_id"] for rec in recommendations}

        # None of the recommended tracks should be in already interacted
        assert len(recommended_tracks & interacted_tracks) == 0

    def test_multiple_users_different_recommendations(
        self, sample_interaction_matrix, sample_user_ids, sample_track_ids
    ):
        """Test that different users get different recommendations."""
        recommender = CollaborativeFilteringRecommender(
            n_factors=10,
            iterations=10,
        )
        recommender.fit(sample_interaction_matrix, sample_user_ids, sample_track_ids)

        recs_user_0 = recommender.recommend_for_user("user_0", n_recommendations=10)
        recs_user_1 = recommender.recommend_for_user("user_1", n_recommendations=10)

        tracks_0 = [r["track_id"] for r in recs_user_0]
        tracks_1 = [r["track_id"] for r in recs_user_1]

        # Different users should generally get at least some different recommendations
        # (not guaranteed but highly likely with random data)
        assert tracks_0 != tracks_1 or len(set(tracks_0) ^ set(tracks_1)) > 0


class TestCollaborativeFilteringIntegration:
    """Integration tests for CF model with synthetic data."""

    def test_load_from_synthetic_data(self):
        """Test loading model trained on synthetic data."""
        import os

        from app.ml.model_persistence import load_model

        # Check if model exists
        model_path = "data/models/collaborative_latest.joblib"
        if not os.path.exists(model_path):
            pytest.skip("Collaborative model not trained yet")

        model = load_model("collaborative")
        assert model is not None
        assert model.is_fitted
        assert len(model.user_mapping) > 0
        assert len(model.track_mapping) > 0

    def test_recommend_from_loaded_model(self):
        """Test recommendations from loaded model."""
        import os

        from app.ml.model_persistence import load_model

        model_path = "data/models/collaborative_latest.joblib"
        if not os.path.exists(model_path):
            pytest.skip("Collaborative model not trained yet")

        model = load_model("collaborative")

        # Get a valid user ID from the model
        user_id = list(model.user_mapping.keys())[0]

        recommendations = model.recommend_for_user(user_id, n_recommendations=10)
        assert len(recommendations) == 10
        assert all("track_id" in r for r in recommendations)
