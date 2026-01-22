"""
Mood analysis service using sentiment analysis
"""


class MoodAnalyzerService:
    """Service for analyzing mood from text."""

    # Emotion to (valence, energy) mapping based on Russell's Circumplex Model
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
                return_all_scores=True,
            )
        except Exception as e:
            print(f"Emotion classifier not available: {e}")

        self._initialized = True

    def analyze_text(self, text):
        """
        Analyze text for mood/emotion.

        Args:
            text: Input text to analyze

        Returns:
            dict: Mood analysis results
        """
        self._lazy_init()

        result = {
            "primary_emotion": "neutral",
            "confidence": 0.5,
            "valence": 0.5,
            "arousal": 0.5,
            "all_emotions": {},
        }

        # VADER sentiment analysis for valence
        if self.vader:
            vader_scores = self.vader.polarity_scores(text)
            result["valence"] = (vader_scores["compound"] + 1) / 2  # Normalize to 0-1

        # Transformer-based emotion classification
        if self.emotion_classifier:
            try:
                emotions = self.emotion_classifier(text)[0]
                emotion_dict = {e["label"].lower(): e["score"] for e in emotions}
                result["all_emotions"] = emotion_dict

                primary = max(emotions, key=lambda x: x["score"])
                result["primary_emotion"] = primary["label"].lower()
                result["confidence"] = primary["score"]
                result["arousal"] = self._emotion_to_arousal(primary["label"])
            except Exception as e:
                print(f"Error in emotion classification: {e}")

        return result

    def _emotion_to_arousal(self, emotion):
        """Map emotion to arousal level."""
        arousal_map = {
            "anger": 0.85,
            "fear": 0.75,
            "surprise": 0.7,
            "joy": 0.65,
            "sadness": 0.3,
            "disgust": 0.5,
            "neutral": 0.5,
        }
        return arousal_map.get(emotion.lower(), 0.5)

    def get_target_features(self, emotion):
        """
        Get target audio features for an emotion.

        Args:
            emotion: Emotion string

        Returns:
            dict: Target valence and energy values
        """
        valence, energy = self.EMOTION_MAP.get(emotion.lower(), (0.5, 0.5))
        return {"target_valence": valence, "target_energy": energy}
