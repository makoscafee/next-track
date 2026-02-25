"""
Cold start strategy for new and anonymous users.

Provides intelligent fallback recommendations when collaborative filtering
is unavailable (no user history). Uses a priority cascade:
1. Genre-preference based (if genres provided)
2. Feature-preference based (if user has stored preferences)
3. Popularity-based (default fallback)
"""

import logging
from typing import Dict, List, Optional, Tuple

import pandas as pd

from app.ml.baselines import PopularityBaseline
from app.ml.content_based import ContentBasedRecommender

logger = logging.getLogger(__name__)

# Map energy preference labels to numeric ranges
ENERGY_PREFERENCE_MAP = {
    "high": {"energy": 0.7, "danceability": 0.65},
    "medium": {"energy": 0.5, "danceability": 0.5},
    "low": {"energy": 0.3, "danceability": 0.35},
}

# Map mood preference labels to valence/energy targets
MOOD_PREFERENCE_MAP = {
    "happy": {"valence": 0.75, "energy": 0.65},
    "calm": {"valence": 0.55, "energy": 0.3},
    "energetic": {"valence": 0.6, "energy": 0.8},
    "melancholic": {"valence": 0.25, "energy": 0.35},
    "focused": {"valence": 0.45, "energy": 0.55},
}


class ColdStartRecommender:
    """
    Handles recommendations for new users without interaction history.
    """

    def __init__(self):
        self.popularity_model = PopularityBaseline()
        self.content_model: Optional[ContentBasedRecommender] = None
        self.tracks_df: Optional[pd.DataFrame] = None
        self.is_initialized = False

    def initialize(
        self,
        tracks_df: pd.DataFrame,
        content_model: Optional[ContentBasedRecommender] = None,
    ):
        """
        Initialize cold start recommender with dataset and models.

        Args:
            tracks_df: Full tracks DataFrame with 'id', 'popularity', audio features
            content_model: Fitted content-based model for preference-based recs
        """
        self.tracks_df = tracks_df
        self.content_model = content_model

        # Fit popularity model on dataset
        self.popularity_model.fit(tracks_df=tracks_df)

        self.is_initialized = True
        logger.info(
            f"Cold start recommender initialized with {len(tracks_df)} tracks"
        )

    @staticmethod
    def is_cold_start(
        user_id: Optional[str], collab_model
    ) -> bool:
        """
        Check if a user is in the cold start state.

        Args:
            user_id: User identifier (None for anonymous)
            collab_model: Collaborative filtering model to check user existence

        Returns:
            True if user has no collaborative filtering data
        """
        if not user_id:
            return True
        if not collab_model or not collab_model.is_fitted:
            return True
        return user_id not in getattr(collab_model, "user_mapping", {})

    def recommend_popular(
        self, n: int = 10, exclude_tracks: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Return most popular tracks from dataset.

        Args:
            n: Number of recommendations
            exclude_tracks: Track IDs to exclude

        Returns:
            List of track recommendation dicts
        """
        if not self.popularity_model.is_fitted:
            return []

        recs = self.popularity_model.recommend(
            n_recommendations=n, exclude_tracks=exclude_tracks
        )

        # Normalize popularity scores to 0-1
        if recs:
            max_score = max(r["score"] for r in recs)
            if max_score > 0:
                for r in recs:
                    r["score"] = r["score"] / max_score
                    r["source"] = "cold_start_popular"

        return recs

    def recommend_for_genres(
        self,
        genres: List[str],
        n: int = 10,
        exclude_tracks: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Recommend tracks matching genre preferences using the genres column
        (enriched from artists.csv). Falls back to artist/track name search
        if genres column is unavailable.

        Args:
            genres: List of genre/style keywords (e.g. ["rock", "jazz"])
            n: Number of recommendations
            exclude_tracks: Track IDs to exclude

        Returns:
            List of track recommendation dicts
        """
        if self.tracks_df is None or not genres:
            return []

        exclude_set = set(exclude_tracks or [])
        genres_lower = [g.lower().strip() for g in genres]

        # Primary: use actual genre metadata from artists.csv
        if "genres" in self.tracks_df.columns:
            def _matches_genre(track_genres):
                if not isinstance(track_genres, list) or not track_genres:
                    return False
                for tg in track_genres:
                    tg_lower = tg.lower()
                    for query in genres_lower:
                        if query in tg_lower:
                            return True
                return False

            mask = self.tracks_df["genres"].apply(_matches_genre)
        else:
            # Fallback: search artist/track names
            mask = pd.Series(False, index=self.tracks_df.index)
            artists_lower = self.tracks_df["artists"].str.lower().fillna("")
            name_lower = self.tracks_df["name"].str.lower().fillna("")
            for genre in genres_lower:
                mask = mask | artists_lower.str.contains(genre, na=False)
                mask = mask | name_lower.str.contains(genre, na=False)

        matched = self.tracks_df[mask].copy()

        # Exclude tracks
        if exclude_set:
            id_col = "id" if "id" in matched.columns else "track_id"
            matched = matched[~matched[id_col].isin(exclude_set)]

        if matched.empty:
            return []

        # Rank by popularity
        if "popularity" in matched.columns:
            matched = matched.sort_values("popularity", ascending=False)

        id_col = "id" if "id" in matched.columns else "track_id"
        results = matched.head(n)

        max_pop = results["popularity"].max() if "popularity" in results.columns else 1
        max_pop = max(max_pop, 1)

        return [
            {
                "track_id": row[id_col],
                "score": float(row.get("popularity", 0)) / max_pop,
                "source": "cold_start_genre",
            }
            for _, row in results.iterrows()
        ]

    def recommend_for_preferences(
        self,
        preferences: Dict,
        n: int = 10,
        exclude_tracks: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Recommend tracks based on user's stored audio feature preferences.
        Uses the content-based model with synthesized feature vector.

        Args:
            preferences: Dict with optional keys: preferred_valence, preferred_energy,
                         preferred_danceability, energy_preference, mood_preference
            n: Number of recommendations
            exclude_tracks: Track IDs to exclude

        Returns:
            List of track recommendation dicts
        """
        if not self.content_model or not self.content_model.is_fitted:
            return []

        # Build target feature vector from preferences
        features = {
            "danceability": 0.5,
            "energy": 0.5,
            "valence": 0.5,
            "tempo": 0.5,  # Already normalized
            "acousticness": 0.5,
            "instrumentalness": 0.5,
            "speechiness": 0.5,
        }

        # Apply direct feature preferences
        if preferences.get("preferred_valence") is not None:
            features["valence"] = float(preferences["preferred_valence"])
        if preferences.get("preferred_energy") is not None:
            features["energy"] = float(preferences["preferred_energy"])
        if preferences.get("preferred_danceability") is not None:
            features["danceability"] = float(preferences["preferred_danceability"])

        # Apply energy preference label
        energy_pref = preferences.get("energy_preference")
        if energy_pref and energy_pref in ENERGY_PREFERENCE_MAP:
            for key, val in ENERGY_PREFERENCE_MAP[energy_pref].items():
                features[key] = val

        # Apply mood preference label
        mood_pref = preferences.get("mood_preference")
        if mood_pref and mood_pref in MOOD_PREFERENCE_MAP:
            for key, val in MOOD_PREFERENCE_MAP[mood_pref].items():
                features[key] = val

        recs = self.content_model.recommend(features, n_recommendations=n)

        # Filter excluded tracks and tag source
        exclude_set = set(exclude_tracks or [])
        results = []
        for r in recs:
            if r["track_id"] not in exclude_set:
                results.append(
                    {
                        "track_id": r["track_id"],
                        "score": r["similarity_score"],
                        "source": "cold_start_preferences",
                    }
                )
        return results[:n]

    def get_cold_start_recommendations(
        self,
        user_id: Optional[str] = None,
        preferred_genres: Optional[List[str]] = None,
        preferences: Optional[Dict] = None,
        context: Optional[Dict] = None,
        n: int = 10,
        exclude_tracks: Optional[List[str]] = None,
    ) -> Tuple[List[Dict], str]:
        """
        Main entry point for cold start recommendations.

        Priority cascade:
        1. Genre-based (if preferred_genres provided)
        2. Preference-based (if user preferences available)
        3. Popularity-based (default fallback)

        Args:
            user_id: Optional user identifier
            preferred_genres: List of genre keywords
            preferences: User preference dict (feature targets)
            context: Context dict (time_of_day, activity, weather)
            n: Number of recommendations
            exclude_tracks: Track IDs to exclude

        Returns:
            Tuple of (recommendations list, strategy name used)
        """
        if not self.is_initialized:
            return [], "uninitialized"

        # Strategy 1: Genre-based
        if preferred_genres:
            recs = self.recommend_for_genres(preferred_genres, n, exclude_tracks)
            if recs:
                logger.info(
                    f"Cold start: genre strategy returned {len(recs)} recs "
                    f"for genres {preferred_genres}"
                )
                return recs, "genre"

        # Strategy 2: Preference-based (content model with user preferences)
        if preferences:
            has_preferences = any(
                preferences.get(k) is not None
                for k in [
                    "preferred_valence",
                    "preferred_energy",
                    "preferred_danceability",
                    "energy_preference",
                    "mood_preference",
                ]
            )
            if has_preferences:
                recs = self.recommend_for_preferences(preferences, n, exclude_tracks)
                if recs:
                    logger.info(
                        f"Cold start: preference strategy returned {len(recs)} recs"
                    )
                    return recs, "preferences"

        # Strategy 3: Popularity fallback
        recs = self.recommend_popular(n, exclude_tracks)
        logger.info(f"Cold start: popularity fallback returned {len(recs)} recs")
        return recs, "popular"
