"""
Content-based filtering recommendation model
Uses audio features to find similar tracks
"""

from typing import Dict, List, Optional, Union

import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler


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

    def __init__(self, n_neighbors: int = 50, algorithm: str = "auto"):
        """
        Initialize the content-based recommender.

        Args:
            n_neighbors: Number of neighbors for K-NN
            algorithm: K-NN algorithm ('auto', 'ball_tree', 'kd_tree', 'brute')
        """
        self.n_neighbors = n_neighbors
        self.algorithm = algorithm
        self.scaler = StandardScaler()
        self.nn_model = NearestNeighbors(
            n_neighbors=n_neighbors, metric="cosine", algorithm=algorithm
        )
        self.track_ids = None
        self._track_id_to_idx: Dict[str, int] = {}
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
        self._track_id_to_idx = {
            track_id: idx for idx, track_id in enumerate(self.track_ids)
        }
        self.is_fitted = True

    def _features_to_array(self, features: Union[Dict, List, np.ndarray]) -> np.ndarray:
        """Convert features to numpy array."""
        if isinstance(features, dict):
            return np.array([features.get(f, 0) for f in self.FEATURES])
        return np.asarray(features)

    def recommend(
        self,
        seed_track_features: Union[Dict, List, np.ndarray],
        n_recommendations: int = 10,
    ) -> List[Dict]:
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

        features = self._features_to_array(seed_track_features)
        X = self.scaler.transform(features.reshape(1, -1))
        distances, indices = self.nn_model.kneighbors(
            X, n_neighbors=min(n_recommendations + 1, self.n_neighbors)
        )

        recommendations = []
        for idx, dist in zip(indices[0][1:], distances[0][1:]):  # Skip seed
            recommendations.append(
                {
                    "track_id": self.track_ids[idx],
                    "similarity_score": float(1 - dist),
                }
            )
        return recommendations

    def recommend_batch(
        self,
        seed_features_list: List[Union[Dict, List, np.ndarray]],
        n_recommendations: int = 10,
    ) -> List[List[Dict]]:
        """
        Get recommendations for multiple seeds in a single batch.

        More efficient than calling recommend() multiple times.

        Args:
            seed_features_list: List of feature dicts/arrays
            n_recommendations: Number of recommendations per seed

        Returns:
            list: List of recommendation lists, one per seed
        """
        if not self.is_fitted or not seed_features_list:
            return [[] for _ in seed_features_list]

        # Convert all features to array
        features_array = np.array(
            [self._features_to_array(f) for f in seed_features_list]
        )
        X = self.scaler.transform(features_array)

        # Batch K-NN query
        distances, indices = self.nn_model.kneighbors(
            X, n_neighbors=min(n_recommendations + 1, self.n_neighbors)
        )

        # Build results for each seed
        all_recommendations = []
        for seed_idx in range(len(seed_features_list)):
            recommendations = []
            for idx, dist in zip(indices[seed_idx][1:], distances[seed_idx][1:]):
                recommendations.append(
                    {
                        "track_id": self.track_ids[idx],
                        "similarity_score": float(1 - dist),
                    }
                )
            all_recommendations.append(recommendations)

        return all_recommendations

    def recommend_from_track_id(
        self, track_id: str, n_recommendations: int = 10
    ) -> List[Dict]:
        """
        Get similar tracks to a track by ID.

        Args:
            track_id: ID of the seed track
            n_recommendations: Number of tracks to recommend

        Returns:
            list: Recommendations with track_id and similarity_score
        """
        if not self.is_fitted:
            return []

        # O(1) lookup using index
        idx = self._track_id_to_idx.get(track_id)
        if idx is None:
            return []

        distances, indices = self.nn_model.kneighbors(
            self.nn_model._fit_X[idx : idx + 1], n_neighbors=n_recommendations + 1
        )

        recommendations = []
        for neighbor_idx, dist in zip(indices[0], distances[0]):
            if neighbor_idx != idx:  # Skip the seed track
                recommendations.append(
                    {
                        "track_id": self.track_ids[neighbor_idx],
                        "similarity_score": float(1 - dist),
                    }
                )
        return recommendations[:n_recommendations]

    def recommend_from_track_ids_batch(
        self, track_ids: List[str], n_recommendations: int = 10
    ) -> List[List[Dict]]:
        """
        Get recommendations for multiple track IDs in a single batch.

        Args:
            track_ids: List of seed track IDs
            n_recommendations: Number of recommendations per seed

        Returns:
            list: List of recommendation lists, one per seed
        """
        if not self.is_fitted or not track_ids:
            return [[] for _ in track_ids]

        # Get indices for valid track IDs
        valid_indices = []
        valid_positions = []
        for pos, track_id in enumerate(track_ids):
            idx = self._track_id_to_idx.get(track_id)
            if idx is not None:
                valid_indices.append(idx)
                valid_positions.append(pos)

        if not valid_indices:
            return [[] for _ in track_ids]

        # Batch K-NN query
        X = self.nn_model._fit_X[valid_indices]
        distances, indices = self.nn_model.kneighbors(
            X, n_neighbors=n_recommendations + 1
        )

        # Build results
        all_recommendations = [[] for _ in track_ids]
        for i, (pos, seed_idx) in enumerate(zip(valid_positions, valid_indices)):
            recommendations = []
            for neighbor_idx, dist in zip(indices[i], distances[i]):
                if neighbor_idx != seed_idx:
                    recommendations.append(
                        {
                            "track_id": self.track_ids[neighbor_idx],
                            "similarity_score": float(1 - dist),
                        }
                    )
            all_recommendations[pos] = recommendations[:n_recommendations]

        return all_recommendations

    def get_track_features(self, track_id: str) -> Optional[Dict]:
        """
        Get the stored features for a track ID.

        Args:
            track_id: Track ID to look up

        Returns:
            dict: Feature values or None if not found
        """
        if not self.is_fitted:
            return None

        idx = self._track_id_to_idx.get(track_id)
        if idx is None:
            return None

        # Get original (scaled) features and inverse transform
        scaled_features = self.nn_model._fit_X[idx]
        original_features = self.scaler.inverse_transform(
            scaled_features.reshape(1, -1)
        )[0]

        return {f: float(v) for f, v in zip(self.FEATURES, original_features)}
