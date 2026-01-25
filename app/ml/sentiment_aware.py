"""
Sentiment-aware recommendation model.

Maps detected mood to music features using Valence-Arousal model based on
Russell's Circumplex Model of Affect.

Reference: Russell, J. A. (1980). A circumplex model of affect.
"""

from typing import Any, Dict, List, Optional

import numpy as np


class SentimentAwareRecommender:
    """
    Maps user's detected emotion to appropriate music.
    Uses Russell's Circumplex Model of Affect.

    Valence (positivity) -> Music Valence
    Arousal (energy) -> Music Energy

    Supports context-aware recommendations that adjust target features
    based on time of day, activity, and other contextual factors.
    """

    # Research-backed Valence-Arousal mapping based on Russell's Circumplex Model
    # Format: emotion -> (valence, arousal)
    EMOTION_MAP = {
        # High valence, high arousal (Q1 - Excited/Happy)
        "joy": (0.85, 0.72),
        "happy": (0.80, 0.65),
        "excited": (0.75, 0.88),
        "elated": (0.82, 0.80),
        "enthusiastic": (0.70, 0.82),
        # High valence, low arousal (Q4 - Calm/Relaxed)
        "calm": (0.62, 0.28),
        "relaxed": (0.68, 0.22),
        "peaceful": (0.60, 0.18),
        "serene": (0.65, 0.15),
        "content": (0.70, 0.35),
        # Low valence, low arousal (Q3 - Sad/Depressed)
        "sad": (0.18, 0.28),
        "sadness": (0.18, 0.28),
        "melancholic": (0.28, 0.35),
        "depressed": (0.12, 0.20),
        "lonely": (0.22, 0.30),
        "bored": (0.35, 0.18),
        # Low valence, high arousal (Q2 - Angry/Anxious)
        "angry": (0.15, 0.88),
        "anger": (0.15, 0.88),
        "anxious": (0.30, 0.75),
        "fear": (0.22, 0.82),
        "stressed": (0.28, 0.78),
        "frustrated": (0.25, 0.72),
        "tense": (0.32, 0.70),
        # Moderate/Mixed emotions
        "surprise": (0.55, 0.78),
        "disgust": (0.20, 0.55),
        "neutral": (0.50, 0.45),
        "nostalgic": (0.45, 0.38),
        "hopeful": (0.65, 0.55),
        "energetic": (0.62, 0.85),
    }

    # Mapping from transformer model output to our emotion set
    TRANSFORMER_EMOTION_MAP = {
        "joy": "joy",
        "sadness": "sad",
        "anger": "angry",
        "fear": "fear",
        "surprise": "surprise",
        "disgust": "disgust",
        "neutral": "neutral",
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

    def _normalize_emotion(self, emotion: str) -> str:
        """Normalize emotion string to our mapping."""
        emotion_lower = emotion.lower()
        if emotion_lower in self.TRANSFORMER_EMOTION_MAP:
            return self.TRANSFORMER_EMOTION_MAP[emotion_lower]
        return emotion_lower

    def _get_target_va(
        self, emotion: str, context: Optional[Dict[str, Any]] = None
    ) -> tuple:
        """
        Get target valence/arousal for emotion with optional context adjustment.

        Args:
            emotion: Emotion string
            context: Optional context dict with time_of_day, activity, weather

        Returns:
            tuple: (target_valence, target_energy)
        """
        emotion_norm = self._normalize_emotion(emotion)
        target_valence, target_energy = self.EMOTION_MAP.get(emotion_norm, (0.5, 0.45))

        # Apply context modifiers if provided
        if context:
            target_valence, target_energy = self._apply_context_modifiers(
                target_valence, target_energy, context
            )

        return target_valence, target_energy

    def _apply_context_modifiers(
        self, valence: float, arousal: float, context: Dict[str, Any]
    ) -> tuple:
        """
        Apply context-based modifiers to valence and arousal.

        Args:
            valence: Base valence
            arousal: Base arousal
            context: Context dict with time_of_day, activity, weather keys

        Returns:
            tuple: (modified_valence, modified_arousal)
        """
        # Context modifiers (valence_delta, arousal_delta)
        time_modifiers = {
            "morning": (0.05, 0.10),
            "afternoon": (0.0, 0.0),
            "evening": (0.0, -0.08),
            "night": (-0.02, -0.15),
        }

        activity_modifiers = {
            "workout": (0.08, 0.20),
            "work": (-0.02, 0.05),
            "relaxation": (0.05, -0.20),
            "party": (0.10, 0.25),
            "commute": (0.0, 0.0),
            "focus": (0.0, 0.10),
            "social": (0.08, 0.10),
        }

        weather_modifiers = {
            "sunny": (0.08, 0.05),
            "rainy": (-0.05, -0.08),
            "cloudy": (-0.03, -0.03),
            "cold": (-0.02, -0.05),
            "hot": (0.02, 0.05),
        }

        v_mod, a_mod = 0.0, 0.0

        if context.get("time_of_day"):
            mods = time_modifiers.get(context["time_of_day"], (0, 0))
            v_mod += mods[0]
            a_mod += mods[1]

        if context.get("activity"):
            mods = activity_modifiers.get(context["activity"], (0, 0))
            v_mod += mods[0]
            a_mod += mods[1]

        if context.get("weather"):
            mods = weather_modifiers.get(context["weather"], (0, 0))
            v_mod += mods[0]
            a_mod += mods[1]

        return (
            max(0.0, min(1.0, valence + v_mod)),
            max(0.0, min(1.0, arousal + a_mod)),
        )

    def recommend_for_mood(
        self,
        detected_emotion: str,
        n_recommendations: int = 10,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find tracks matching the emotional state with optional context.

        Args:
            detected_emotion: String emotion (e.g., 'happy', 'sad')
            n_recommendations: Number of tracks to return
            context: Optional context dict for recommendation adjustment

        Returns:
            list: Recommendations with mood matching scores
        """
        if not self.is_fitted:
            return []

        target_valence, target_energy = self._get_target_va(detected_emotion, context)

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
                "mood_score": float(1 / (1 + row["mood_distance"])),
                "target_valence": target_valence,
                "target_energy": target_energy,
            }
            for _, row in recommendations.iterrows()
        ]

    def recommend_for_valence_energy(
        self,
        target_valence: float,
        target_energy: float,
        n_recommendations: int = 10,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find tracks matching specific valence and energy values.

        Args:
            target_valence: Target valence (0-1)
            target_energy: Target energy (0-1)
            n_recommendations: Number of tracks
            context: Optional context for additional adjustment

        Returns:
            list: Matching tracks
        """
        if not self.is_fitted:
            return []

        # Apply context modifiers if provided
        if context:
            target_valence, target_energy = self._apply_context_modifiers(
                target_valence, target_energy, context
            )

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
                "target_valence": target_valence,
                "target_energy": target_energy,
            }
            for _, row in recommendations.iterrows()
        ]

    def get_emotion_for_features(self, valence: float, energy: float) -> str:
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

    def get_quadrant(self, valence: float, arousal: float) -> str:
        """
        Get the emotional quadrant for given valence/arousal.

        Quadrants based on Russell's Circumplex Model:
        - Q1: High valence, High arousal (Happy/Excited)
        - Q2: Low valence, High arousal (Angry/Anxious)
        - Q3: Low valence, Low arousal (Sad/Depressed)
        - Q4: High valence, Low arousal (Calm/Relaxed)

        Args:
            valence: Valence value (0-1)
            arousal: Arousal value (0-1)

        Returns:
            str: Quadrant name and description
        """
        if valence >= 0.5 and arousal >= 0.5:
            return "Q1_excited"
        elif valence < 0.5 and arousal >= 0.5:
            return "Q2_tense"
        elif valence < 0.5 and arousal < 0.5:
            return "Q3_sad"
        else:
            return "Q4_calm"
