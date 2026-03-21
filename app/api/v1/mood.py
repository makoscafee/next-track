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
        Analyse free-text input and return emotion + suggested audio features.
        ---
        tags:
          - Mood
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required: [text]
              properties:
                text:
                  type: string
                  example: I'm feeling anxious but determined before my morning workout
                include_context:
                  type: boolean
                  description: Extract time/activity/weather context from text
                  default: true
                context:
                  type: object
                  description: Explicit context override
                  properties:
                    time_of_day:
                      type: string
                      enum: [morning, afternoon, evening, night]
                    activity:
                      type: string
                      enum: [workout, work, relaxation, party, commute, focus, social]
                    weather:
                      type: string
                      enum: [sunny, rainy, cloudy, cold, hot]
                source:
                  type: string
                  description: Caller label for logging
                  example: user_input
        responses:
          200:
            description: Mood analysis result
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: success
                mood_analysis:
                  type: object
                  properties:
                    primary_emotion:
                      type: string
                      example: joy
                    confidence:
                      type: number
                      example: 0.92
                    valence:
                      type: number
                      description: Positivity 0–1
                      example: 0.85
                    arousal:
                      type: number
                      description: Energy level 0–1
                      example: 0.65
                    all_emotions:
                      type: object
                    context:
                      type: object
                    context_adjustment:
                      type: object
                      properties:
                        valence_delta:
                          type: number
                        arousal_delta:
                          type: number
                suggested_music_features:
                  type: object
                  description: Recommended audio feature target ranges
                metadata:
                  type: object
          400:
            description: Missing text field
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
        Get recommendations for a mood (or analyse text to detect mood first).
        ---
        tags:
          - Mood
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                mood:
                  type: string
                  description: Explicit mood (required if text not supplied)
                  enum: [happy, sad, energetic, calm, melancholic, angry, anxious, neutral, excited, peaceful, relaxed, focused]
                  example: happy
                text:
                  type: string
                  description: Free text — mood is detected automatically
                  example: I'm feeling great for my morning workout!
                limit:
                  type: integer
                  default: 10
                  maximum: 50
                include_context:
                  type: boolean
                  default: true
                context:
                  type: object
                  properties:
                    time_of_day:
                      type: string
                      enum: [morning, afternoon, evening, night]
                    activity:
                      type: string
                      enum: [workout, work, relaxation, party, commute, focus, social]
                    weather:
                      type: string
                      enum: [sunny, rainy, cloudy, cold, hot]
        responses:
          200:
            description: Mood-matched recommendations
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: success
                mood:
                  type: string
                  example: happy
                target_features:
                  type: object
                  description: Audio feature ranges used for retrieval
                context:
                  type: object
                context_adjustment:
                  type: object
                recommendations:
                  type: array
                  items:
                    type: object
                metadata:
                  type: object
                  properties:
                    count:
                      type: integer
                    text_analyzed:
                      type: boolean
                    context_enabled:
                      type: boolean
          400:
            description: Neither mood nor text supplied
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
