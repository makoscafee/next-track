"""
Mood analysis service using sentiment analysis.

Uses Russell's Circumplex Model of Affect for emotion-to-music mapping.
Reference: Russell, J. A. (1980). A circumplex model of affect.
"""

import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple


class MoodAnalyzerService:
    """Service for analyzing mood from text with context awareness."""

    # Research-backed Valence-Arousal mapping based on Russell's Circumplex Model
    # Values calibrated from affective computing literature
    # Format: emotion -> (valence, arousal, intensity_weight)
    # intensity_weight modulates how much confidence affects the final values
    EMOTION_VA_MAP = {
        # High valence, high arousal (Q1 - Excited/Happy)
        "joy": (0.85, 0.72, 1.0),
        "happy": (0.80, 0.65, 0.9),
        "excited": (0.75, 0.88, 1.0),
        "elated": (0.82, 0.80, 1.0),
        "enthusiastic": (0.70, 0.82, 0.9),
        # High valence, low arousal (Q4 - Calm/Relaxed)
        "calm": (0.62, 0.28, 0.7),
        "relaxed": (0.68, 0.22, 0.8),
        "peaceful": (0.60, 0.18, 0.7),
        "serene": (0.65, 0.15, 0.8),
        "content": (0.70, 0.35, 0.7),
        # Low valence, low arousal (Q3 - Sad/Depressed)
        "sad": (0.18, 0.28, 1.0),
        "sadness": (0.18, 0.28, 1.0),
        "melancholic": (0.28, 0.35, 0.9),
        "depressed": (0.12, 0.20, 1.0),
        "lonely": (0.22, 0.30, 0.9),
        "bored": (0.35, 0.18, 0.6),
        # Low valence, high arousal (Q2 - Angry/Anxious)
        "angry": (0.15, 0.88, 1.0),
        "anger": (0.15, 0.88, 1.0),
        "anxious": (0.30, 0.75, 0.9),
        "fear": (0.22, 0.82, 1.0),
        "stressed": (0.28, 0.78, 0.9),
        "frustrated": (0.25, 0.72, 0.9),
        "tense": (0.32, 0.70, 0.8),
        # Moderate/Mixed emotions
        "surprise": (0.55, 0.78, 0.8),  # Can be positive or negative
        "disgust": (0.20, 0.55, 0.9),
        "neutral": (0.50, 0.45, 0.3),
        "nostalgic": (0.45, 0.38, 0.8),
        "hopeful": (0.65, 0.55, 0.8),
        "energetic": (0.62, 0.85, 0.9),
    }

    # Mapping from transformer model emotions to our extended emotion set
    TRANSFORMER_EMOTION_MAP = {
        "joy": "joy",
        "sadness": "sad",
        "anger": "angry",
        "fear": "fear",
        "surprise": "surprise",
        "disgust": "disgust",
        "neutral": "neutral",
    }

    # Context detection patterns
    TIME_PATTERNS = {
        "morning": r"\b(morning|wake up|breakfast|sunrise|dawn)\b",
        "afternoon": r"\b(afternoon|lunch|midday)\b",
        "evening": r"\b(evening|dinner|sunset|dusk)\b",
        "night": r"\b(night|sleep|bedtime|midnight|late)\b",
    }

    ACTIVITY_PATTERNS = {
        "workout": r"\b(workout|exercise|gym|run|running|training|fitness|jog)\b",
        "work": r"\b(work|office|meeting|deadline|project|study|studying)\b",
        "relaxation": r"\b(relax|chill|unwind|rest|meditate|meditation)\b",
        "party": r"\b(party|celebration|dance|dancing|club|fun)\b",
        "commute": r"\b(commute|driving|drive|car|train|bus|travel)\b",
        "focus": r"\b(focus|concentrate|concentration|productive|coding|reading)\b",
        "social": r"\b(friends|hanging out|date|dinner party|gathering)\b",
    }

    WEATHER_PATTERNS = {
        "sunny": r"\b(sunny|sunshine|bright|clear sky)\b",
        "rainy": r"\b(rain|rainy|raining|storm|thunder)\b",
        "cloudy": r"\b(cloudy|overcast|grey|gray)\b",
        "cold": r"\b(cold|freezing|winter|snow|snowy)\b",
        "hot": r"\b(hot|summer|heat|warm)\b",
    }

    # Context modifiers for valence/arousal
    CONTEXT_MODIFIERS = {
        # Time-based modifiers (valence_mod, arousal_mod)
        "time": {
            "morning": (0.05, 0.10),  # Slightly more positive, energetic
            "afternoon": (0.0, 0.0),
            "evening": (0.0, -0.08),  # Slightly lower energy
            "night": (-0.02, -0.15),  # Calmer
        },
        # Activity-based modifiers
        "activity": {
            "workout": (0.08, 0.20),  # High energy
            "work": (-0.02, 0.05),
            "relaxation": (0.05, -0.20),  # Low energy
            "party": (0.10, 0.25),  # High energy, positive
            "commute": (0.0, 0.0),
            "focus": (0.0, 0.10),  # Moderate energy
            "social": (0.08, 0.10),
        },
        # Weather-based modifiers
        "weather": {
            "sunny": (0.08, 0.05),
            "rainy": (-0.05, -0.08),
            "cloudy": (-0.03, -0.03),
            "cold": (-0.02, -0.05),
            "hot": (0.02, 0.05),
        },
    }

    def __init__(self):
        """Initialize mood analyzer."""
        self.vader = None
        self.emotion_classifier = None
        self._initialized = False

    def _lazy_init(self):
        """Lazy initialization of NLP models."""
        if self._initialized:
            return

        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

            self.vader = SentimentIntensityAnalyzer()
        except ImportError:
            print("VADER not available")

        try:
            from transformers import pipeline

            self.emotion_classifier = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                top_k=None,  # Returns all scores (replaces deprecated return_all_scores)
            )
        except Exception as e:
            print(f"Emotion classifier not available: {e}")

        self._initialized = True

    def detect_context(
        self, text: str, timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Detect contextual information from text and timestamp.

        Args:
            text: Input text to analyze
            timestamp: Optional timestamp for time-of-day context

        Returns:
            dict: Detected context information
        """
        text_lower = text.lower()
        context = {
            "time_of_day": None,
            "activity": None,
            "weather": None,
            "detected_from_text": {},
        }

        # Detect time of day from text
        for time_period, pattern in self.TIME_PATTERNS.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                context["time_of_day"] = time_period
                context["detected_from_text"]["time"] = True
                break

        # If no time detected from text, use timestamp
        if not context["time_of_day"] and timestamp:
            hour = timestamp.hour
            if 5 <= hour < 12:
                context["time_of_day"] = "morning"
            elif 12 <= hour < 17:
                context["time_of_day"] = "afternoon"
            elif 17 <= hour < 21:
                context["time_of_day"] = "evening"
            else:
                context["time_of_day"] = "night"
            context["detected_from_text"]["time"] = False

        # Detect activity
        for activity, pattern in self.ACTIVITY_PATTERNS.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                context["activity"] = activity
                context["detected_from_text"]["activity"] = True
                break

        # Detect weather mentions
        for weather, pattern in self.WEATHER_PATTERNS.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                context["weather"] = weather
                context["detected_from_text"]["weather"] = True
                break

        return context

    def _apply_context_modifiers(
        self, valence: float, arousal: float, context: Dict[str, Any]
    ) -> Tuple[float, float]:
        """
        Apply context-based modifiers to valence and arousal.

        Args:
            valence: Base valence value
            arousal: Base arousal value
            context: Detected context dict

        Returns:
            tuple: Modified (valence, arousal)
        """
        v_mod, a_mod = 0.0, 0.0

        # Time modifier
        if context.get("time_of_day"):
            time_mods = self.CONTEXT_MODIFIERS["time"].get(
                context["time_of_day"], (0, 0)
            )
            v_mod += time_mods[0]
            a_mod += time_mods[1]

        # Activity modifier
        if context.get("activity"):
            act_mods = self.CONTEXT_MODIFIERS["activity"].get(
                context["activity"], (0, 0)
            )
            v_mod += act_mods[0]
            a_mod += act_mods[1]

        # Weather modifier
        if context.get("weather"):
            weather_mods = self.CONTEXT_MODIFIERS["weather"].get(
                context["weather"], (0, 0)
            )
            v_mod += weather_mods[0]
            a_mod += weather_mods[1]

        # Apply modifiers with clamping
        new_valence = max(0.0, min(1.0, valence + v_mod))
        new_arousal = max(0.0, min(1.0, arousal + a_mod))

        return new_valence, new_arousal

    def _compute_intensity_adjusted_va(
        self, emotion: str, confidence: float
    ) -> Tuple[float, float]:
        """
        Compute intensity-adjusted valence and arousal.

        Higher confidence = values closer to the emotion's extremes.
        Lower confidence = values closer to neutral.

        Args:
            emotion: Detected emotion
            confidence: Confidence score (0-1)

        Returns:
            tuple: (valence, arousal)
        """
        emotion_lower = emotion.lower()

        # Map transformer emotions to our extended set
        if emotion_lower in self.TRANSFORMER_EMOTION_MAP:
            emotion_lower = self.TRANSFORMER_EMOTION_MAP[emotion_lower]

        # Get base values
        base_v, base_a, intensity_weight = self.EMOTION_VA_MAP.get(
            emotion_lower, (0.5, 0.5, 0.5)
        )

        # Neutral point
        neutral_v, neutral_a = 0.5, 0.45

        # Compute intensity factor based on confidence and emotion's intensity weight
        intensity = confidence * intensity_weight

        # Interpolate between neutral and emotion values based on intensity
        valence = neutral_v + (base_v - neutral_v) * intensity
        arousal = neutral_a + (base_a - neutral_a) * intensity

        return valence, arousal

    def analyze_text(
        self,
        text: str,
        timestamp: Optional[datetime] = None,
        include_context: bool = True,
    ) -> Dict[str, Any]:
        """
        Analyze text for mood/emotion with context awareness.

        Args:
            text: Input text to analyze
            timestamp: Optional timestamp for time-of-day context
            include_context: Whether to detect and apply context modifiers

        Returns:
            dict: Mood analysis results with context
        """
        self._lazy_init()

        result = {
            "primary_emotion": "neutral",
            "confidence": 0.5,
            "valence": 0.5,
            "arousal": 0.5,
            "all_emotions": {},
            "context": {},
            "intensity_adjusted": False,
        }

        # Detect context if enabled
        if include_context:
            result["context"] = self.detect_context(text, timestamp)

        # VADER sentiment analysis for baseline valence
        vader_valence = 0.5
        if self.vader:
            vader_scores = self.vader.polarity_scores(text)
            vader_valence = (vader_scores["compound"] + 1) / 2  # Normalize to 0-1
            result["vader_compound"] = vader_scores["compound"]

        # Transformer-based emotion classification
        if self.emotion_classifier:
            try:
                emotions = self.emotion_classifier(text)[0]
                emotion_dict = {e["label"].lower(): e["score"] for e in emotions}
                result["all_emotions"] = emotion_dict

                primary = max(emotions, key=lambda x: x["score"])
                result["primary_emotion"] = primary["label"].lower()
                result["confidence"] = primary["score"]

                # Compute intensity-adjusted valence and arousal
                valence, arousal = self._compute_intensity_adjusted_va(
                    primary["label"], primary["score"]
                )

                # Blend with VADER valence for robustness (70% transformer, 30% VADER)
                result["valence"] = 0.7 * valence + 0.3 * vader_valence
                result["arousal"] = arousal
                result["intensity_adjusted"] = True

            except Exception as e:
                print(f"Error in emotion classification: {e}")
                result["valence"] = vader_valence
        else:
            result["valence"] = vader_valence

        # Apply context modifiers
        if include_context and result["context"]:
            orig_valence, orig_arousal = result["valence"], result["arousal"]
            result["valence"], result["arousal"] = self._apply_context_modifiers(
                result["valence"], result["arousal"], result["context"]
            )
            result["context_adjustment"] = {
                "valence_delta": result["valence"] - orig_valence,
                "arousal_delta": result["arousal"] - orig_arousal,
            }

        return result

    def _emotion_to_arousal(self, emotion: str) -> float:
        """Map emotion to arousal level (legacy method for compatibility)."""
        emotion_lower = emotion.lower()
        if emotion_lower in self.TRANSFORMER_EMOTION_MAP:
            emotion_lower = self.TRANSFORMER_EMOTION_MAP[emotion_lower]

        if emotion_lower in self.EMOTION_VA_MAP:
            return self.EMOTION_VA_MAP[emotion_lower][1]

        # Fallback
        arousal_map = {
            "anger": 0.88,
            "fear": 0.82,
            "surprise": 0.78,
            "joy": 0.72,
            "sadness": 0.28,
            "disgust": 0.55,
            "neutral": 0.45,
        }
        return arousal_map.get(emotion_lower, 0.45)

    def get_target_features(
        self, emotion: str, context: Optional[Dict[str, Any]] = None
    ):
        """
        Get target audio features for an emotion with optional context adjustment.

        Args:
            emotion: Emotion string
            context: Optional context dict for modifiers

        Returns:
            dict: Target valence and energy values with context info
        """
        emotion_lower = emotion.lower()

        # Map transformer emotions
        if emotion_lower in self.TRANSFORMER_EMOTION_MAP:
            emotion_lower = self.TRANSFORMER_EMOTION_MAP[emotion_lower]

        # Get base values from VA map
        if emotion_lower in self.EMOTION_VA_MAP:
            valence, energy, _ = self.EMOTION_VA_MAP[emotion_lower]
        else:
            valence, energy = 0.5, 0.5

        result = {
            "target_valence": valence,
            "target_energy": energy,
            "emotion": emotion_lower,
        }

        # Apply context modifiers if provided
        if context:
            adj_valence, adj_energy = self._apply_context_modifiers(
                valence, energy, context
            )
            result["context_adjusted_valence"] = adj_valence
            result["context_adjusted_energy"] = adj_energy
            result["context"] = context

        return result
