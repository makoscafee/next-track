"""
Content-based filtering recommendation model
Uses audio features to find similar tracks
"""

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors


class ContentBasedRecommender:
    """
    Recommends songs based on audio feature similarity.
    Uses cosine similarity on normalized feature vectors.
    """

    FEATURES = [
        "danceability",
        "energy",
        "valence",
        "tempo",
        "acousticness",
        "instrumentalness",
        "speechiness",
    ]

    def __init__(self, n_neighbors=50):
        """
        Initialize the content-based recommender.

        Args:
            n_neighbors: Number of neighbors for K-NN
        """
        self.n_neighbors = n_neighbors
        self.scaler = StandardScaler()
        self.nn_model = NearestNeighbors(
            n_neighbors=n_neighbors, metric="cosine", algorithm="brute"
        )
        self.track_ids = None
        self.is_fitted = False

    def fit(self, track_features_df):
        """
        Fit model on track feature dataframe.

        Args:
            track_features_df: DataFrame with track features and 'track_id' column
        """
        X = self.scaler.fit_transform(track_features_df[self.FEATURES])
        self.nn_model.fit(X)
        self.track_ids = track_features_df["track_id"].values
        self.is_fitted = True

    def recommend(self, seed_track_features, n_recommendations=10):
        """
        Get similar tracks to seed.

        Args:
            seed_track_features: Dict or array of feature values
            n_recommendations: Number of tracks to recommend

        Returns:
            list: Recommendations with track_id and similarity_score
        """
        if not self.is_fitted:
            return []

        # Convert dict to array if needed
        if isinstance(seed_track_features, dict):
            features = [seed_track_features.get(f, 0) for f in self.FEATURES]
        else:
            features = seed_track_features

        X = self.scaler.transform([features])
        distances, indices = self.nn_model.kneighbors(
            X, n_neighbors=min(n_recommendations + 1, self.n_neighbors)
        )

        recommendations = []
        for idx, dist in zip(indices[0][1:], distances[0][1:]):  # Skip seed
            recommendations.append(
                {
                    "track_id": self.track_ids[idx],
                    "similarity_score": float(
                        1 - dist
                    ),  # Convert distance to similarity
                }
            )
        return recommendations

    def recommend_from_track_id(self, track_id, n_recommendations=10):
        """
        Get similar tracks to a track by ID.

        Args:
            track_id: ID of the seed track
            n_recommendations: Number of tracks to recommend

        Returns:
            list: Recommendations with track_id and similarity_score
        """
        if not self.is_fitted or track_id not in self.track_ids:
            return []

        idx = np.where(self.track_ids == track_id)[0][0]
        distances, indices = self.nn_model.kneighbors(
            self.nn_model._fit_X[idx : idx + 1], n_neighbors=n_recommendations + 1
        )

        recommendations = []
        for i, (neighbor_idx, dist) in enumerate(zip(indices[0], distances[0])):
            if neighbor_idx != idx:  # Skip the seed track
                recommendations.append(
                    {
                        "track_id": self.track_ids[neighbor_idx],
                        "similarity_score": float(1 - dist),
                    }
                )
        return recommendations[:n_recommendations]
