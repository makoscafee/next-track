"""
Collaborative filtering recommendation model
Uses matrix factorization on user-track interactions
"""

import numpy as np


class CollaborativeFilteringRecommender:
    """
    Uses SVD/ALS matrix factorization for collaborative filtering.
    Predicts user preferences based on similar users' behavior.
    """

    def __init__(self, n_factors=50, regularization=0.1, iterations=50):
        """
        Initialize collaborative filtering recommender.

        Args:
            n_factors: Number of latent factors
            regularization: Regularization parameter
            iterations: Number of training iterations
        """
        self.n_factors = n_factors
        self.regularization = regularization
        self.iterations = iterations
        self.model = None
        self.user_mapping = None
        self.track_mapping = None
        self.is_fitted = False

    def fit(self, interaction_matrix, user_ids, track_ids):
        """
        Fit on user-item interaction matrix.

        Args:
            interaction_matrix: scipy.sparse matrix (users x tracks)
            user_ids: Array of user IDs corresponding to matrix rows
            track_ids: Array of track IDs corresponding to matrix columns
        """
        try:
            from implicit.als import AlternatingLeastSquares

            self.model = AlternatingLeastSquares(
                factors=self.n_factors,
                regularization=self.regularization,
                iterations=self.iterations,
                use_gpu=False,
            )
            self.model.fit(interaction_matrix)
            self.user_mapping = {uid: idx for idx, uid in enumerate(user_ids)}
            self.track_mapping = {tid: idx for idx, tid in enumerate(track_ids)}
            self.reverse_track_mapping = {
                idx: tid for tid, idx in self.track_mapping.items()
            }
            self.interaction_matrix = interaction_matrix
            self.is_fitted = True
        except ImportError:
            print("implicit library not installed. CF recommendations unavailable.")
            self.is_fitted = False

    def recommend_for_user(
        self, user_id, n_recommendations=10, filter_already_liked=True
    ):
        """
        Get recommendations for a specific user.

        Args:
            user_id: User identifier
            n_recommendations: Number of recommendations
            filter_already_liked: Whether to filter out already interacted tracks

        Returns:
            list: Recommendations with track_id and cf_score
        """
        if not self.is_fitted or user_id not in self.user_mapping:
            return []

        user_idx = self.user_mapping[user_id]

        ids, scores = self.model.recommend(
            user_idx,
            self.interaction_matrix[user_idx],
            N=n_recommendations,
            filter_already_liked_items=filter_already_liked,
        )

        return [
            {"track_id": self.reverse_track_mapping[tid], "cf_score": float(score)}
            for tid, score in zip(ids, scores)
        ]

    def get_similar_users(self, user_id, n_users=10):
        """
        Find users similar to a given user.

        Args:
            user_id: User identifier
            n_users: Number of similar users to find

        Returns:
            list: Similar user IDs with similarity scores
        """
        if not self.is_fitted or user_id not in self.user_mapping:
            return []

        user_idx = self.user_mapping[user_id]
        similar = self.model.similar_users(user_idx, N=n_users + 1)

        reverse_user_mapping = {idx: uid for uid, idx in self.user_mapping.items()}
        return [
            {"user_id": reverse_user_mapping[idx], "similarity": float(score)}
            for idx, score in zip(similar[0][1:], similar[1][1:])  # Skip self
        ]
