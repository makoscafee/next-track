"""
Mood analysis API endpoints with context awareness.

Supports time-of-day, activity, and weather context for improved recommendations.
"""

from datetime import datetime

from flask import request
from flask_restful import Resource

from app.services import MoodAnalyzerService, RecommendationService

# Initialize services
mood_analyzer = MoodAnalyzerService()
recommendation_service = RecommendationService()


class MoodAnalyzeResource(Resource):
    """Analyze text for mood/emotion with context detection."""

    def post(self):
        """
        Analyze text input to detect mood with context awareness.

        Request body:
        {
            "text": "I'm feeling great today!",
            "source": "user_input" (optional),
            "include_context": true (optional, default true),
            "context": {  // Optional explicit context override
                "time_of_day": "morning",
                "activity": "workout",
                "weather": "sunny"
            }
        }

        Returns:
        {
            "status": "success",
            "mood_analysis": {
                "primary_emotion": "joy",
                "confidence": 0.92,
                "valence": 0.85,
                "arousal": 0.65,
                "all_emotions": {...},
                "context": {
                    "time_of_day": "morning",
                    "activity": "workout",
                    "detected_from_text": {...}
                },
                "context_adjustment": {
                    "valence_delta": 0.13,
                    "arousal_delta": 0.30
                }
            },
            "suggested_music_features": {...}
        }
        """
        data = request.get_json() or {}

        text = data.get("text")
        if not text:
            return {"status": "error", "message": 'The "text" field is required'}, 400

        # Get context options
        include_context = data.get("include_context", True)
        explicit_context = data.get("context")

        # Use current timestamp for time-of-day detection
        timestamp = datetime.now()

        # Analyze mood with context
        analysis = mood_analyzer.analyze_text(
            text, timestamp=timestamp, include_context=include_context
        )

        # Override with explicit context if provided
        if explicit_context:
            analysis["context"].update(explicit_context)
            # Re-apply context modifiers with explicit context
            if analysis.get("intensity_adjusted"):
                orig_v = analysis["valence"] - analysis.get(
                    "context_adjustment", {}
                ).get("valence_delta", 0)
                orig_a = analysis["arousal"] - analysis.get(
                    "context_adjustment", {}
                ).get("arousal_delta", 0)
                new_v, new_a = mood_analyzer._apply_context_modifiers(
                    orig_v, orig_a, analysis["context"]
                )
                analysis["valence"] = new_v
                analysis["arousal"] = new_a
                analysis["context_adjustment"] = {
                    "valence_delta": new_v - orig_v,
                    "arousal_delta": new_a - orig_a,
                }

        # Get suggested music features based on detected emotion and context
        target_features = mood_analyzer.get_target_features(
            analysis["primary_emotion"],
            context=analysis.get("context") if include_context else None,
        )

        return {
            "status": "success",
            "mood_analysis": analysis,
            "suggested_music_features": target_features,
            "metadata": {
                "text_length": len(text),
                "source": data.get("source", "user_input"),
                "context_enabled": include_context,
                "timestamp": timestamp.isoformat(),
            },
        }, 200


class MoodRecommendResource(Resource):
    """Get context-aware recommendations based on mood."""

    def post(self):
        """
        Get recommendations matching a specific mood with context awareness.

        Request body:
        {
            "mood": "happy",
            "limit": 10,
            "include_context": true (optional),
            "context": {  // Optional explicit context
                "time_of_day": "morning",
                "activity": "workout",
                "weather": "sunny"
            }
        }

        OR analyze text first:
        {
            "text": "I'm feeling great for my morning workout!",
            "limit": 10
        }

        Returns:
        {
            "status": "success",
            "mood": "happy",
            "context": {...},
            "target_features": {...},
            "recommendations": [...]
        }
        """
        data = request.get_json() or {}

        mood = data.get("mood")
        text = data.get("text")
        limit = min(data.get("limit", 10), 50)
        include_context = data.get("include_context", True)
        explicit_context = data.get("context")

        # Variables to track analysis results
        analysis = None
        context = explicit_context or {}

        # If text provided, analyze it first
        if text and not mood:
            timestamp = datetime.now()
            analysis = mood_analyzer.analyze_text(
                text, timestamp=timestamp, include_context=include_context
            )
            mood = analysis["primary_emotion"]

            # Use detected context if no explicit context provided
            if not explicit_context and analysis.get("context"):
                context = analysis["context"]

        # Override/merge with explicit context
        if explicit_context:
            context.update(explicit_context)

        if not mood:
            return {
                "status": "error",
                "message": 'Either "mood" or "text" field is required',
            }, 400

        # Initialize models and get recommendations
        recommendation_service.initialize_models()

        recommendations = recommendation_service.get_recommendations(
            mood=mood, limit=limit, context=context if include_context else None
        )

        # Get target features for the mood with context
        target_features = mood_analyzer.get_target_features(
            mood, context=context if include_context else None
        )

        response = {
            "status": "success",
            "mood": mood,
            "target_features": target_features,
            "recommendations": recommendations,
            "metadata": {
                "count": len(recommendations),
                "text_analyzed": text is not None,
                "context_enabled": include_context,
            },
        }

        # Include context info if enabled
        if include_context and context:
            response["context"] = context
            if analysis and analysis.get("context_adjustment"):
                response["context_adjustment"] = analysis["context_adjustment"]

        return response, 200
