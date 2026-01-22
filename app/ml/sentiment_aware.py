"""
Sentiment-aware recommendation model
Maps detected mood to music features using Valence-Arousal model
"""

import numpy as np


class SentimentAwareRecommender:
    """
    Maps user's detected emotion to appropriate music.
    Uses Russell's Circumplex Model of Affect.

    Valence (positivity) -> Music Valence
    Arousal (energy) -> Music Energy
    """

    # Emotion to (valence, energy) mapping
    EMOTION_MAP = {
        "happy": (0.8, 0.7),
        "excited": (0.7, 0.9),
        "calm": (0.6, 0.3),
        "relaxed": (0.65, 0.25),
        "sad": (0.2, 0.3),
        "angry": (0.3, 0.85),
        "anxious": (0.4, 0.7),
        "melancholic": (0.35, 0.4),
        "energetic": (0.65, 0.85),
        "peaceful": (0.55, 0.2),
        "joy": (0.8, 0.65),
        "fear": (0.3, 0.75),
        "surprise": (0.6, 0.7),
        "disgust": (0.25, 0.5),
        "neutral": (0.5, 0.5),
    }

    def __init__(self):
        """Initialize sentiment-aware recommender."""
        self.tracks = None
        self.is_fitted = False

    def fit(self, track_features_df):
        """
        Fit on track feature dataframe.

        Args:
            track_features_df: DataFrame with track_id, valence, energy columns
        """
        self.tracks = track_features_df.copy()
        self.is_fitted = True

    def recommend_for_mood(self, detected_emotion, n_recommendations=10):
        """
        Find tracks matching the emotional state.

        Args:
            detected_emotion: String emotion (e.g., 'happy', 'sad')
            n_recommendations: Number of tracks to return

        Returns:
            list: Recommendations with mood matching scores
        """
        if not self.is_fitted:
            return []

        target_valence, target_energy = self.EMOTION_MAP.get(
            detected_emotion.lower(), (0.5, 0.5)
        )

        # Calculate euclidean distance in valence-energy space
        tracks = self.tracks.copy()
        tracks["mood_distance"] = np.sqrt(
            (tracks["valence"] - target_valence) ** 2
            + (tracks["energy"] - target_energy) ** 2
        )

        # Get closest matches
        recommendations = tracks.nsmallest(n_recommendations, "mood_distance")

        return [
            {
                "track_id": row["track_id"],
                "valence": float(row["valence"]),
                "energy": float(row["energy"]),
                "mood_distance": float(row["mood_distance"]),
                "mood_score": float(1 / (1 + row["mood_distance"])),  # Convert to score
            }
            for _, row in recommendations.iterrows()
        ]

    def recommend_for_valence_energy(
        self, target_valence, target_energy, n_recommendations=10
    ):
        """
        Find tracks matching specific valence and energy values.

        Args:
            target_valence: Target valence (0-1)
            target_energy: Target energy (0-1)
            n_recommendations: Number of tracks

        Returns:
            list: Matching tracks
        """
        if not self.is_fitted:
            return []

        tracks = self.tracks.copy()
        tracks["mood_distance"] = np.sqrt(
            (tracks["valence"] - target_valence) ** 2
            + (tracks["energy"] - target_energy) ** 2
        )

        recommendations = tracks.nsmallest(n_recommendations, "mood_distance")

        return [
            {
                "track_id": row["track_id"],
                "valence": float(row["valence"]),
                "energy": float(row["energy"]),
                "mood_score": float(1 / (1 + row["mood_distance"])),
            }
            for _, row in recommendations.iterrows()
        ]

    def get_emotion_for_features(self, valence, energy):
        """
        Determine the closest emotion for given valence/energy.

        Args:
            valence: Valence value (0-1)
            energy: Energy value (0-1)

        Returns:
            str: Closest emotion label
        """
        min_distance = float("inf")
        closest_emotion = "neutral"

        for emotion, (v, e) in self.EMOTION_MAP.items():
            distance = np.sqrt((valence - v) ** 2 + (energy - e) ** 2)
            if distance < min_distance:
                min_distance = distance
                closest_emotion = emotion

        return closest_emotion
