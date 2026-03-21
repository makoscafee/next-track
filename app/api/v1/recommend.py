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
        Get hybrid music recommendations.
        ---
        tags:
          - Recommendations
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                user_id:
                  type: string
                  description: User ID for personalisation and A/B testing
                  example: user_123
                seed_tracks:
                  type: array
                  description: Seed tracks to base recommendations on
                  items:
                    type: object
                    properties:
                      name:
                        type: string
                        example: Bohemian Rhapsody
                      artist:
                        type: string
                        example: Queen
                      track_id:
                        type: string
                        example: 4u7EnebtmKWzUH433cf5Qv
                mood:
                  type: string
                  description: Target mood
                  enum: [happy, sad, energetic, calm, melancholic, angry, anxious, neutral, excited, peaceful, relaxed, focused]
                  example: happy
                context:
                  type: object
                  description: Situational context modifiers
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
                limit:
                  type: integer
                  description: Number of recommendations (max 50)
                  default: 10
                  example: 10
                include_explanation:
                  type: boolean
                  description: Include human-readable explanation per track
                  default: false
                diversity_factor:
                  type: number
                  description: MMR diversity level 0 (relevance-only) to 1 (max diversity)
                  minimum: 0
                  maximum: 1
                  example: 0.5
                serendipity_factor:
                  type: number
                  description: Fraction of results replaced with surprising tracks
                  minimum: 0
                  maximum: 1
                  example: 0.0
                preferred_genres:
                  type: array
                  items:
                    type: string
                  description: Filter results to these genres
                  example: [rock, electronic]
                exclude_explicit:
                  type: boolean
                  description: Remove explicit tracks from results
                  default: false
        responses:
          200:
            description: Recommendations returned successfully
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: success
                recommendations:
                  type: array
                  items:
                    type: object
                    properties:
                      name:
                        type: string
                        example: Bohemian Rhapsody
                      artist:
                        type: string
                        example: Queen
                      track_id:
                        type: string
                        example: 4u7EnebtmKWzUH433cf5Qv
                      score:
                        type: number
                        example: 0.87
                      source:
                        type: string
                        example: hybrid
                      explanation:
                        type: string
                        example: Matches your energetic mood with high danceability
                      audio_features:
                        type: object
                metadata:
                  type: object
                  properties:
                    count:
                      type: integer
                    mood:
                      type: string
                    sources:
                      type: array
                      items:
                        type: string
          400:
            description: Invalid input parameters
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

        # Optional explicit filter
        exclude_explicit = bool(data.get("exclude_explicit", False))

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
            exclude_explicit=exclude_explicit,
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
        ---
        tags:
          - Recommendations
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required: [artist, track]
              properties:
                artist:
                  type: string
                  example: Queen
                track:
                  type: string
                  example: Bohemian Rhapsody
                limit:
                  type: integer
                  default: 10
                  maximum: 50
        responses:
          200:
            description: Similar tracks returned
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: success
                similar_tracks:
                  type: array
                  items:
                    type: object
                seed_track:
                  type: object
                  properties:
                    artist:
                      type: string
                    track:
                      type: string
                metadata:
                  type: object
                  properties:
                    count:
                      type: integer
          400:
            description: Missing artist or track field
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
        Onboard a new user and return cold-start recommendations.
        ---
        tags:
          - Recommendations
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required: [user_id]
              properties:
                user_id:
                  type: string
                  example: user_123
                preferred_genres:
                  type: array
                  items:
                    type: string
                  example: [rock, electronic, jazz]
                energy_preference:
                  type: string
                  enum: [high, medium, low]
                  example: high
                mood_preference:
                  type: string
                  enum: [happy, calm, energetic, melancholic, focused]
                  example: energetic
                limit:
                  type: integer
                  default: 10
                  maximum: 50
        responses:
          200:
            description: User onboarded with initial recommendations
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: success
                user:
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
                    strategy:
                      type: string
                      enum: [genre, feature_preference, popularity, fallback]
                    preferred_genres:
                      type: array
                      items:
                        type: string
          400:
            description: Missing user_id
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
