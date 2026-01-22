"""
Baseline recommendation models for comparison
"""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class PopularityBaseline:
    """
    Popularity-based recommendation baseline.

    Recommends the most popular tracks (by play count or interaction count).
    Used as a baseline to compare against more sophisticated models.
    """

    def __init__(self):
        self.popular_tracks: List[Dict] = []
        self.is_fitted = False

    def fit(self, interactions_df: pd.DataFrame = None, tracks_df: pd.DataFrame = None):
        """
        Fit the popularity model.

        Args:
            interactions_df: DataFrame with user-track interactions
            tracks_df: DataFrame with track popularity scores
        """
        if interactions_df is not None and len(interactions_df) > 0:
            # Calculate popularity from interactions
            if "play_count" in interactions_df.columns:
                popularity = interactions_df.groupby("track_id")["play_count"].sum()
            else:
                popularity = interactions_df.groupby("track_id").size()

            popularity = popularity.sort_values(ascending=False)
            self.popular_tracks = [
                {"track_id": track_id, "popularity_score": float(score)}
                for track_id, score in popularity.items()
            ]

        elif tracks_df is not None and "popularity" in tracks_df.columns:
            # Use existing popularity scores from dataset
            sorted_tracks = tracks_df.sort_values("popularity", ascending=False)
            id_col = "id" if "id" in sorted_tracks.columns else "track_id"

            self.popular_tracks = [
                {"track_id": row[id_col], "popularity_score": float(row["popularity"])}
                for _, row in sorted_tracks.iterrows()
            ]

        else:
            logger.warning("No valid data to fit popularity model")
            return

        self.is_fitted = True
        logger.info(
            f"Popularity baseline fitted with {len(self.popular_tracks)} tracks"
        )

    def recommend(
        self,
        user_id: str = None,
        n_recommendations: int = 10,
        exclude_tracks: List[str] = None,
    ) -> List[Dict]:
        """
        Get popularity-based recommendations.

        Args:
            user_id: Ignored (popularity doesn't personalize)
            n_recommendations: Number of recommendations
            exclude_tracks: Track IDs to exclude

        Returns:
            List of recommended tracks with scores
        """
        if not self.is_fitted:
            return []

        exclude_set = set(exclude_tracks or [])

        recommendations = []
        for track in self.popular_tracks:
            if track["track_id"] not in exclude_set:
                recommendations.append(
                    {
                        "track_id": track["track_id"],
                        "score": track["popularity_score"],
                        "source": "popularity_baseline",
                    }
                )

            if len(recommendations) >= n_recommendations:
                break

        return recommendations


class RandomBaseline:
    """
    Random recommendation baseline.

    Recommends random tracks from the catalog.
    Useful as a lower bound baseline.
    """

    def __init__(self, random_state: int = 42):
        self.track_ids: List[str] = []
        self.random_state = random_state
        self.rng = np.random.RandomState(random_state)
        self.is_fitted = False

    def fit(self, tracks_df: pd.DataFrame = None, track_ids: List[str] = None):
        """
        Fit the random model with available track IDs.

        Args:
            tracks_df: DataFrame with track data
            track_ids: List of track IDs
        """
        if tracks_df is not None:
            id_col = "id" if "id" in tracks_df.columns else "track_id"
            self.track_ids = tracks_df[id_col].tolist()
        elif track_ids is not None:
            self.track_ids = track_ids
        else:
            logger.warning("No track IDs provided for random baseline")
            return

        self.is_fitted = True
        logger.info(f"Random baseline fitted with {len(self.track_ids)} tracks")

    def recommend(
        self,
        user_id: str = None,
        n_recommendations: int = 10,
        exclude_tracks: List[str] = None,
    ) -> List[Dict]:
        """
        Get random recommendations.

        Args:
            user_id: Ignored
            n_recommendations: Number of recommendations
            exclude_tracks: Track IDs to exclude

        Returns:
            List of randomly selected tracks
        """
        if not self.is_fitted:
            return []

        exclude_set = set(exclude_tracks or [])
        available_tracks = [t for t in self.track_ids if t not in exclude_set]

        if not available_tracks:
            return []

        n_to_sample = min(n_recommendations, len(available_tracks))
        sampled = self.rng.choice(available_tracks, size=n_to_sample, replace=False)

        return [
            {
                "track_id": track_id,
                "score": 1.0 / (i + 1),  # Arbitrary decreasing score
                "source": "random_baseline",
            }
            for i, track_id in enumerate(sampled)
        ]


class ContentBasedBaseline:
    """
    Simple content-based baseline using average feature matching.

    For users with history, recommends tracks similar to their average preferences.
    """

    FEATURES = ["danceability", "energy", "valence", "acousticness", "instrumentalness"]

    def __init__(self):
        self.tracks_df: Optional[pd.DataFrame] = None
        self.is_fitted = False

    def fit(self, tracks_df: pd.DataFrame):
        """
        Fit with track features.

        Args:
            tracks_df: DataFrame with track features
        """
        self.tracks_df = tracks_df.copy()

        # Ensure we have required columns
        available_features = [f for f in self.FEATURES if f in self.tracks_df.columns]
        if not available_features:
            logger.warning("No audio features found in tracks DataFrame")
            return

        self.features = available_features
        self.is_fitted = True
        logger.info(f"Content-based baseline fitted with features: {self.features}")

    def recommend(
        self,
        user_id: str = None,
        n_recommendations: int = 10,
        exclude_tracks: List[str] = None,
        user_history_df: pd.DataFrame = None,
        target_features: Dict[str, float] = None,
    ) -> List[Dict]:
        """
        Get content-based recommendations.

        Args:
            user_id: User ID (ignored, for API compatibility)
            n_recommendations: Number of recommendations
            exclude_tracks: Track IDs to exclude
            user_history_df: User's listened tracks with features
            target_features: Target feature values to match

        Returns:
            List of recommended tracks
        """
        if not self.is_fitted:
            return []

        # Calculate target features from user history or use provided
        if target_features is None and user_history_df is not None:
            target_features = {}
            for feature in self.features:
                if feature in user_history_df.columns:
                    target_features[feature] = user_history_df[feature].mean()

        if not target_features:
            # Default to middle values
            target_features = {f: 0.5 for f in self.features}

        # Calculate distance from target
        tracks = self.tracks_df.copy()

        exclude_set = set(exclude_tracks or [])
        id_col = "id" if "id" in tracks.columns else "track_id"
        tracks = tracks[~tracks[id_col].isin(exclude_set)]

        # Euclidean distance in feature space
        distance = np.zeros(len(tracks))
        for feature in self.features:
            if feature in tracks.columns and feature in target_features:
                distance += (
                    tracks[feature].fillna(0.5) - target_features[feature]
                ) ** 2

        tracks["distance"] = np.sqrt(distance)
        tracks = tracks.sort_values("distance")

        return [
            {
                "track_id": row[id_col],
                "score": float(1 / (1 + row["distance"])),
                "source": "content_baseline",
            }
            for _, row in tracks.head(n_recommendations).iterrows()
        ]
