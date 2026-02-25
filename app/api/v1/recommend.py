"""
Recommendation API endpoints
"""

from flask import request
from flask_restful import Resource

from app.services import RecommendationService
from app.services.user_service import get_user_service

# Initialize service (will be properly managed with app context later)
recommendation_service = RecommendationService()


class RecommendResource(Resource):
    """Get personalized recommendations."""

    def post(self):
        """
        Get hybrid recommendations based on user, seed tracks, and mood.

        Request body:
        {
            "user_id": "string" (optional) - For personalization and A/B testing,
            "seed_tracks": [
                {"name": "track name", "artist": "artist name"},
                ...
            ],
            "mood": "happy" (optional),
            "context": {  // optional
                "time_of_day": "morning|afternoon|evening|night",
                "activity": "workout|work|relaxation|party|commute|focus|social",
                "weather": "sunny|rainy|cloudy|cold|hot"
            },
            "limit": 10,
            "include_explanation": false (optional) - Include detailed explanations,
            "diversity_factor": 0.3 (optional) - Override A/B test (0-1),
            "serendipity_factor": 0.0 (optional) - Override A/B test (0-1)
        }

        Returns:
        {
            "status": "success",
            "recommendations": [...],
            "metadata": {...}
        }
        """
        data = request.get_json() or {}

        user_id = data.get("user_id")
        seed_tracks = data.get("seed_tracks", [])
        mood = data.get("mood")
        context = data.get("context")
        limit = min(data.get("limit", 10), 50)  # Cap at 50
        include_explanation = data.get("include_explanation", False)

        # Optional genre preferences for cold start
        preferred_genres = data.get("preferred_genres", [])

        # Optional overrides for diversity/serendipity
        diversity_factor = data.get("diversity_factor")
        serendipity_factor = data.get("serendipity_factor")

        # Validate diversity/serendipity if provided
        if diversity_factor is not None:
            try:
                diversity_factor = float(diversity_factor)
                if not 0 <= diversity_factor <= 1:
                    return {
                        "status": "error",
                        "message": "diversity_factor must be between 0 and 1",
                    }, 400
            except (TypeError, ValueError):
                return {
                    "status": "error",
                    "message": "diversity_factor must be a number",
                }, 400

        if serendipity_factor is not None:
            try:
                serendipity_factor = float(serendipity_factor)
                if not 0 <= serendipity_factor <= 1:
                    return {
                        "status": "error",
                        "message": "serendipity_factor must be between 0 and 1",
                    }, 400
            except (TypeError, ValueError):
                return {
                    "status": "error",
                    "message": "serendipity_factor must be a number",
                }, 400

        # Initialize models if needed
        recommendation_service.initialize_models()

        # Get recommendations
        recommendations = recommendation_service.get_recommendations(
            user_id=user_id,
            seed_tracks=seed_tracks,
            mood=mood,
            limit=limit,
            context=context,
            include_explanation=include_explanation,
            diversity_factor=diversity_factor,
            serendipity_factor=serendipity_factor,
            preferred_genres=preferred_genres or None,
        )

        return {
            "status": "success",
            "recommendations": recommendations,
            "metadata": {
                "count": len(recommendations),
                "seed_tracks_provided": len(seed_tracks),
                "mood": mood,
                "context": context,
                "sources": list(
                    set(r.get("source", "unknown") for r in recommendations)
                ),
                "explanations_included": include_explanation,
            },
        }, 200


class SimilarTracksResource(Resource):
    """Find similar tracks based on Last.fm data and audio features."""

    def post(self):
        """
        Find tracks similar to a given track.

        Request body:
        {
            "artist": "artist name",
            "track": "track name",
            "limit": 10
        }

        Returns:
        {
            "status": "success",
            "similar_tracks": [...],
            "seed_track": {...}
        }
        """
        data = request.get_json() or {}

        artist = data.get("artist")
        track = data.get("track")
        limit = min(data.get("limit", 10), 50)

        if not artist or not track:
            return {
                "status": "error",
                "message": 'Both "artist" and "track" fields are required',
            }, 400

        # Get similar tracks
        similar = recommendation_service.get_similar_tracks(
            artist=artist, track=track, limit=limit
        )

        return {
            "status": "success",
            "similar_tracks": similar,
            "seed_track": {"artist": artist, "track": track},
            "metadata": {"count": len(similar)},
        }, 200


class OnboardingResource(Resource):
    """Genre-preference onboarding for new users."""

    def post(self):
        """
        Onboard a new user with genre/mood preferences and return initial recommendations.

        Request body:
        {
            "user_id": "string" (required),
            "preferred_genres": ["rock", "electronic", "jazz"] (optional),
            "energy_preference": "high" | "medium" | "low" (optional),
            "mood_preference": "happy" | "calm" | "energetic" | "melancholic" | "focused" (optional),
            "limit": 10
        }

        Returns:
        {
            "status": "success",
            "user": {...},
            "recommendations": [...],
            "strategy": "genre" | "preferences" | "popular"
        }
        """
        data = request.get_json() or {}

        user_id = data.get("user_id")
        if not user_id:
            return {"status": "error", "message": "user_id is required"}, 400

        preferred_genres = data.get("preferred_genres", [])
        energy_preference = data.get("energy_preference")
        mood_preference = data.get("mood_preference")
        limit = min(data.get("limit", 10), 50)

        # Create or get user and store preferences
        service = get_user_service()
        user = service.get_or_create_user(external_id=user_id)

        preferences = {}
        if preferred_genres:
            preferences["preferred_genres"] = preferred_genres
        if energy_preference:
            preferences["energy_preference"] = energy_preference
        if mood_preference:
            preferences["mood_preference"] = mood_preference

        if preferences:
            service.update_user_preferences(user_id, preferences)
            user = service.get_user(user_id)

        # Initialize models and get cold start recommendations
        recommendation_service.initialize_models()

        cold_start = recommendation_service.cold_start
        if cold_start.is_initialized:
            recs, strategy = cold_start.get_cold_start_recommendations(
                user_id=user_id,
                preferred_genres=preferred_genres or None,
                preferences=preferences or None,
                n=limit,
            )
            # Enrich with metadata
            recommendations = recommendation_service._enrich_cold_start_recs(
                recs, strategy
            )
        else:
            recommendations = recommendation_service._get_fallback_recommendations(
                limit
            )
            strategy = "fallback"

        return {
            "status": "success",
            "user": user.to_dict() if user else None,
            "recommendations": recommendations,
            "metadata": {
                "count": len(recommendations),
                "strategy": strategy,
                "preferred_genres": preferred_genres,
            },
        }, 200
