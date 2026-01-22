"""
Mood analysis API endpoints
"""

from flask import request
from flask_restful import Resource

from app.services import MoodAnalyzerService, RecommendationService

# Initialize services
mood_analyzer = MoodAnalyzerService()
recommendation_service = RecommendationService()


class MoodAnalyzeResource(Resource):
    """Analyze text for mood/emotion."""

    def post(self):
        """
        Analyze text input to detect mood.

        Request body:
        {
            "text": "I'm feeling great today!",
            "source": "user_input" (optional)
        }

        Returns:
        {
            "status": "success",
            "mood_analysis": {
                "primary_emotion": "joy",
                "confidence": 0.92,
                "valence": 0.85,
                "arousal": 0.65,
                "all_emotions": {...}
            },
            "suggested_music_features": {...}
        }
        """
        data = request.get_json() or {}

        text = data.get("text")
        if not text:
            return {"status": "error", "message": 'The "text" field is required'}, 400

        # Analyze mood
        analysis = mood_analyzer.analyze_text(text)

        # Get suggested music features based on detected emotion
        target_features = mood_analyzer.get_target_features(analysis["primary_emotion"])

        return {
            "status": "success",
            "mood_analysis": analysis,
            "suggested_music_features": target_features,
            "metadata": {
                "text_length": len(text),
                "source": data.get("source", "user_input"),
            },
        }, 200


class MoodRecommendResource(Resource):
    """Get recommendations based on mood."""

    def post(self):
        """
        Get recommendations matching a specific mood.

        Request body:
        {
            "mood": "happy",
            "limit": 10
        }

        OR analyze text first:
        {
            "text": "I'm feeling great today!",
            "limit": 10
        }

        Returns:
        {
            "status": "success",
            "mood": "happy",
            "recommendations": [...]
        }
        """
        data = request.get_json() or {}

        mood = data.get("mood")
        text = data.get("text")
        limit = min(data.get("limit", 10), 50)

        # If text provided, analyze it first
        if text and not mood:
            analysis = mood_analyzer.analyze_text(text)
            mood = analysis["primary_emotion"]

        if not mood:
            return {
                "status": "error",
                "message": 'Either "mood" or "text" field is required',
            }, 400

        # Initialize models and get recommendations
        recommendation_service.initialize_models()

        recommendations = recommendation_service.get_recommendations(
            mood=mood, limit=limit
        )

        # Get target features for the mood
        target_features = mood_analyzer.get_target_features(mood)

        return {
            "status": "success",
            "mood": mood,
            "target_features": target_features,
            "recommendations": recommendations,
            "metadata": {
                "count": len(recommendations),
                "text_analyzed": text is not None,
            },
        }, 200
