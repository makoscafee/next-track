"""
Tests for mood analyzer service
"""

import pytest

from app.services.mood_analyzer import MoodAnalyzerService


class TestMoodAnalyzerService:
    """Tests for mood analyzer service."""

    def test_initialization(self):
        """Test service initializes correctly."""
        analyzer = MoodAnalyzerService()
        assert analyzer._initialized is False

    def test_emotion_map_exists(self):
        """Test emotion mapping is defined."""
        analyzer = MoodAnalyzerService()
        assert len(analyzer.EMOTION_MAP) > 0
        assert "happy" in analyzer.EMOTION_MAP
        assert "sad" in analyzer.EMOTION_MAP

    def test_get_target_features(self):
        """Test getting target features for emotions."""
        analyzer = MoodAnalyzerService()

        features = analyzer.get_target_features("happy")
        assert "target_valence" in features
        assert "target_energy" in features
        assert 0 <= features["target_valence"] <= 1
        assert 0 <= features["target_energy"] <= 1

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
