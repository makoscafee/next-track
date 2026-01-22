"""
Recommendation API endpoints
"""

from flask import request
from flask_restful import Resource

from app.services import RecommendationService

# Initialize service (will be properly managed with app context later)
recommendation_service = RecommendationService()


class RecommendResource(Resource):
    """Get personalized recommendations."""

    def post(self):
        """
        Get hybrid recommendations based on user, seed tracks, and mood.

        Request body:
        {
            "user_id": "string" (optional),
            "seed_tracks": [
                {"name": "track name", "artist": "artist name"},
                ...
            ],
            "mood": "happy" (optional),
            "limit": 10
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
        limit = min(data.get("limit", 10), 50)  # Cap at 50

        # Initialize models if needed
        recommendation_service.initialize_models()

        # Get recommendations
        recommendations = recommendation_service.get_recommendations(
            user_id=user_id, seed_tracks=seed_tracks, mood=mood, limit=limit
        )

        return {
            "status": "success",
            "recommendations": recommendations,
            "metadata": {
                "count": len(recommendations),
                "seed_tracks_provided": len(seed_tracks),
                "mood": mood,
                "sources": list(
                    set(r.get("source", "unknown") for r in recommendations)
                ),
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
