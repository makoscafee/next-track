"""
Tests for mood analyzer service with context detection.
"""

from datetime import datetime

import pytest

from app.services.mood_analyzer import MoodAnalyzerService


class TestMoodAnalyzerService:
    """Tests for mood analyzer service."""

    def test_initialization(self):
        """Test service initializes correctly."""
        analyzer = MoodAnalyzerService()
        assert analyzer._initialized is False

    def test_emotion_va_map_exists(self):
        """Test emotion VA mapping is defined with proper structure."""
        analyzer = MoodAnalyzerService()
        assert len(analyzer.EMOTION_VA_MAP) > 0
        assert "happy" in analyzer.EMOTION_VA_MAP
        assert "sad" in analyzer.EMOTION_VA_MAP
        assert "joy" in analyzer.EMOTION_VA_MAP

        # Check structure: (valence, arousal, intensity_weight)
        for emotion, values in analyzer.EMOTION_VA_MAP.items():
            assert len(values) == 3
            valence, arousal, intensity = values
            assert 0 <= valence <= 1, f"{emotion} valence out of range"
            assert 0 <= arousal <= 1, f"{emotion} arousal out of range"
            assert 0 <= intensity <= 1, f"{emotion} intensity out of range"

    def test_circumplex_quadrants(self):
        """Test emotions are correctly positioned in Russell's quadrants."""
        analyzer = MoodAnalyzerService()

        # Q1: High valence, high arousal
        joy_v, joy_a, _ = analyzer.EMOTION_VA_MAP["joy"]
        assert joy_v > 0.5 and joy_a > 0.5, "Joy should be in Q1"

        # Q2: Low valence, high arousal
        angry_v, angry_a, _ = analyzer.EMOTION_VA_MAP["angry"]
        assert angry_v < 0.5 and angry_a > 0.5, "Angry should be in Q2"

        # Q3: Low valence, low arousal
        sad_v, sad_a, _ = analyzer.EMOTION_VA_MAP["sad"]
        assert sad_v < 0.5 and sad_a < 0.5, "Sad should be in Q3"

        # Q4: High valence, low arousal
        calm_v, calm_a, _ = analyzer.EMOTION_VA_MAP["calm"]
        assert calm_v > 0.5 and calm_a < 0.5, "Calm should be in Q4"

    def test_get_target_features(self):
        """Test getting target features for emotions."""
        analyzer = MoodAnalyzerService()

        features = analyzer.get_target_features("happy")
        assert "target_valence" in features
        assert "target_energy" in features
        assert "emotion" in features
        assert 0 <= features["target_valence"] <= 1
        assert 0 <= features["target_energy"] <= 1

    def test_get_target_features_with_context(self):
        """Test target features are adjusted with context."""
        analyzer = MoodAnalyzerService()

        # Without context
        base_features = analyzer.get_target_features("happy")

        # With workout context (should increase energy)
        workout_context = {"activity": "workout"}
        workout_features = analyzer.get_target_features(
            "happy", context=workout_context
        )

        assert "context_adjusted_energy" in workout_features
        assert (
            workout_features["context_adjusted_energy"] > base_features["target_energy"]
        )

        # With relaxation context (should decrease energy)
        relax_context = {"activity": "relaxation"}
        relax_features = analyzer.get_target_features("happy", context=relax_context)

        assert (
            relax_features["context_adjusted_energy"] < base_features["target_energy"]
        )

    def test_get_target_features_unknown_emotion(self):
        """Test getting target features for unknown emotion."""
        analyzer = MoodAnalyzerService()

        features = analyzer.get_target_features("unknown_emotion")
        assert features["target_valence"] == 0.5
        assert features["target_energy"] == 0.5

    def test_emotion_to_arousal(self):
        """Test emotion to arousal mapping."""
        analyzer = MoodAnalyzerService()

        # High arousal emotions
        assert analyzer._emotion_to_arousal("anger") > 0.7
        assert analyzer._emotion_to_arousal("fear") > 0.7

        # Low arousal emotions
        assert analyzer._emotion_to_arousal("sadness") < 0.4

    def test_transformer_emotion_mapping(self):
        """Test transformer emotions are mapped correctly."""
        analyzer = MoodAnalyzerService()

        # These are the emotions from j-hartmann model
        transformer_emotions = [
            "joy",
            "sadness",
            "anger",
            "fear",
            "surprise",
            "disgust",
            "neutral",
        ]
        for emotion in transformer_emotions:
            assert emotion in analyzer.TRANSFORMER_EMOTION_MAP


class TestContextDetection:
    """Tests for context detection from text."""

    def test_detect_time_of_day_from_text(self):
        """Test time of day detection from keywords."""
        analyzer = MoodAnalyzerService()

        morning_context = analyzer.detect_context(
            "Good morning, I'm ready for breakfast!"
        )
        assert morning_context["time_of_day"] == "morning"
        assert morning_context["detected_from_text"].get("time") is True

        night_context = analyzer.detect_context("Can't sleep at midnight")
        assert night_context["time_of_day"] == "night"

    def test_detect_time_from_timestamp(self):
        """Test time of day detection from timestamp when not in text."""
        analyzer = MoodAnalyzerService()

        # Morning timestamp (8 AM)
        morning_ts = datetime(2024, 1, 1, 8, 0, 0)
        context = analyzer.detect_context("I feel great today", timestamp=morning_ts)
        assert context["time_of_day"] == "morning"
        assert context["detected_from_text"].get("time") is False

        # Night timestamp (11 PM)
        night_ts = datetime(2024, 1, 1, 23, 0, 0)
        context = analyzer.detect_context("I feel great today", timestamp=night_ts)
        assert context["time_of_day"] == "night"

    def test_detect_activity(self):
        """Test activity detection from text."""
        analyzer = MoodAnalyzerService()

        workout_context = analyzer.detect_context("Getting pumped for my gym workout!")
        assert workout_context["activity"] == "workout"

        work_context = analyzer.detect_context("Busy day at the office with meetings")
        assert work_context["activity"] == "work"

        party_context = analyzer.detect_context("Going to a celebration tonight!")
        assert party_context["activity"] == "party"

    def test_detect_weather(self):
        """Test weather detection from text."""
        analyzer = MoodAnalyzerService()

        sunny_context = analyzer.detect_context("Beautiful sunny day outside!")
        assert sunny_context["weather"] == "sunny"

        rainy_context = analyzer.detect_context("The rain keeps falling")
        assert rainy_context["weather"] == "rainy"

    def test_detect_multiple_contexts(self):
        """Test detecting multiple context types from one text."""
        analyzer = MoodAnalyzerService()

        context = analyzer.detect_context("Morning workout in the sunny weather")
        assert context["time_of_day"] == "morning"
        assert context["activity"] == "workout"
        assert context["weather"] == "sunny"


class TestContextModifiers:
    """Tests for context-based valence/arousal modifiers."""

    def test_workout_increases_energy(self):
        """Test workout context increases arousal."""
        analyzer = MoodAnalyzerService()

        base_v, base_a = 0.5, 0.5
        context = {"activity": "workout"}

        new_v, new_a = analyzer._apply_context_modifiers(base_v, base_a, context)
        assert new_a > base_a, "Workout should increase arousal"

    def test_relaxation_decreases_energy(self):
        """Test relaxation context decreases arousal."""
        analyzer = MoodAnalyzerService()

        base_v, base_a = 0.5, 0.5
        context = {"activity": "relaxation"}

        new_v, new_a = analyzer._apply_context_modifiers(base_v, base_a, context)
        assert new_a < base_a, "Relaxation should decrease arousal"

    def test_sunny_weather_positive_effect(self):
        """Test sunny weather increases valence."""
        analyzer = MoodAnalyzerService()

        base_v, base_a = 0.5, 0.5
        context = {"weather": "sunny"}

        new_v, new_a = analyzer._apply_context_modifiers(base_v, base_a, context)
        assert new_v > base_v, "Sunny weather should increase valence"

    def test_night_time_calmer(self):
        """Test night time decreases arousal."""
        analyzer = MoodAnalyzerService()

        base_v, base_a = 0.5, 0.5
        context = {"time_of_day": "night"}

        new_v, new_a = analyzer._apply_context_modifiers(base_v, base_a, context)
        assert new_a < base_a, "Night should decrease arousal"

    def test_modifiers_stack(self):
        """Test multiple context modifiers combine correctly."""
        analyzer = MoodAnalyzerService()

        base_v, base_a = 0.5, 0.5

        # Single modifier
        single_context = {"activity": "workout"}
        single_v, single_a = analyzer._apply_context_modifiers(
            base_v, base_a, single_context
        )

        # Multiple modifiers (workout + sunny + morning)
        multi_context = {
            "activity": "workout",
            "weather": "sunny",
            "time_of_day": "morning",
        }
        multi_v, multi_a = analyzer._apply_context_modifiers(
            base_v, base_a, multi_context
        )

        # Multiple should have greater effect
        assert multi_a > single_a, "Multiple positive energy contexts should stack"
        assert multi_v > single_v, "Multiple positive valence contexts should stack"

    def test_modifiers_clamped(self):
        """Test modifiers stay within 0-1 bounds."""
        analyzer = MoodAnalyzerService()

        # Start near boundary
        high_v, high_a = 0.95, 0.95
        context = {"activity": "party", "weather": "sunny", "time_of_day": "morning"}

        new_v, new_a = analyzer._apply_context_modifiers(high_v, high_a, context)
        assert new_v <= 1.0, "Valence should be clamped at 1.0"
        assert new_a <= 1.0, "Arousal should be clamped at 1.0"

        # Start near lower boundary
        low_v, low_a = 0.05, 0.05
        context = {"activity": "relaxation", "weather": "rainy", "time_of_day": "night"}

        new_v, new_a = analyzer._apply_context_modifiers(low_v, low_a, context)
        assert new_v >= 0.0, "Valence should be clamped at 0.0"
        assert new_a >= 0.0, "Arousal should be clamped at 0.0"


class TestIntensityModulation:
    """Tests for confidence-based intensity adjustment."""

    def test_high_confidence_stronger_emotion(self):
        """Test high confidence produces values closer to emotion extremes."""
        analyzer = MoodAnalyzerService()

        # High confidence joy
        high_v, high_a = analyzer._compute_intensity_adjusted_va("joy", 0.95)

        # Low confidence joy
        low_v, low_a = analyzer._compute_intensity_adjusted_va("joy", 0.3)

        # High confidence should be further from neutral
        neutral_v, neutral_a = 0.5, 0.45
        high_dist = abs(high_v - neutral_v) + abs(high_a - neutral_a)
        low_dist = abs(low_v - neutral_v) + abs(low_a - neutral_a)

        assert high_dist > low_dist, "High confidence should produce stronger values"

    def test_neutral_stays_neutral(self):
        """Test neutral emotion stays near center regardless of confidence."""
        analyzer = MoodAnalyzerService()

        v, a = analyzer._compute_intensity_adjusted_va("neutral", 0.9)

        # Should be close to neutral point
        assert 0.4 <= v <= 0.6, "Neutral valence should stay near center"
        assert 0.35 <= a <= 0.55, "Neutral arousal should stay near center"
