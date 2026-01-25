"""
User management API endpoints
"""

from flask import request
from flask_restful import Resource

from app.services.user_service import get_user_service


class UserProfileResource(Resource):
    """User profile management."""

    def get(self):
        """
        Get user profile.

        Query params:
            user_id: External user identifier (required)
        """
        user_id = request.args.get("user_id")
        if not user_id:
            return {"status": "error", "message": "user_id is required"}, 400

        service = get_user_service()
        user = service.get_user(user_id)

        if user is None:
            return {"status": "error", "message": "User not found"}, 404

        return {
            "status": "success",
            "user": user.to_dict(),
        }, 200

    def post(self):
        """
        Create or get user profile.

        Body:
            user_id: External user identifier (required)
            email: Optional email
            username: Optional username
            preferences: Optional preferences dict
        """
        data = request.get_json() or {}

        user_id = data.get("user_id")
        if not user_id:
            return {"status": "error", "message": "user_id is required"}, 400

        service = get_user_service()
        user = service.get_or_create_user(
            external_id=user_id,
            email=data.get("email"),
            username=data.get("username"),
        )

        # Update preferences if provided
        if "preferences" in data:
            service.update_user_preferences(user_id, data["preferences"])
            user = service.get_user(user_id)

        return {
            "status": "success",
            "user": user.to_dict(),
        }, 201

    def put(self):
        """
        Update user preferences.

        Body:
            user_id: External user identifier (required)
            preferences: Preferences to update
        """
        data = request.get_json() or {}

        user_id = data.get("user_id")
        if not user_id:
            return {"status": "error", "message": "user_id is required"}, 400

        preferences = data.get("preferences", {})

        service = get_user_service()
        user = service.update_user_preferences(user_id, preferences)

        if user is None:
            return {"status": "error", "message": "User not found"}, 404

        return {
            "status": "success",
            "user": user.to_dict(),
        }, 200


class UserHistoryResource(Resource):
    """User listening history management."""

    def get(self):
        """
        Get user's listening history.

        Query params:
            user_id: External user identifier (required)
            limit: Max interactions (default: 50)
            types: Comma-separated interaction types filter
        """
        user_id = request.args.get("user_id")
        if not user_id:
            return {"status": "error", "message": "user_id is required"}, 400

        limit = request.args.get("limit", 50, type=int)
        types_str = request.args.get("types")
        types = types_str.split(",") if types_str else None

        service = get_user_service()
        history = service.get_user_history(
            user_id, limit=limit, interaction_types=types
        )

        return {
            "status": "success",
            "user_id": user_id,
            "count": len(history),
            "history": history,
        }, 200

    def post(self):
        """
        Record a user-track interaction.

        Body:
            user_id: External user identifier (required)
            track_id: Track identifier (required)
            interaction_type: Type (play, like, save, skip) - default: play
            play_count: Number of plays - default: 1
            rating: Optional rating (1-5)
            mood: Optional mood at time of play
        """
        data = request.get_json() or {}

        user_id = data.get("user_id")
        track_id = data.get("track_id")

        if not user_id:
            return {"status": "error", "message": "user_id is required"}, 400
        if not track_id:
            return {"status": "error", "message": "track_id is required"}, 400

        service = get_user_service()
        interaction = service.record_interaction(
            user_external_id=user_id,
            track_id=track_id,
            interaction_type=data.get("interaction_type", "play"),
            play_count=data.get("play_count", 1),
            rating=data.get("rating"),
            mood=data.get("mood"),
            context=data.get("context"),
        )

        return {
            "status": "success",
            "interaction": interaction.to_dict() if interaction else None,
        }, 201


class UserStatsResource(Resource):
    """User statistics endpoint."""

    def get(self):
        """
        Get user listening statistics.

        Query params:
            user_id: External user identifier (required)
        """
        user_id = request.args.get("user_id")
        if not user_id:
            return {"status": "error", "message": "user_id is required"}, 400

        service = get_user_service()
        stats = service.get_user_stats(user_id)

        if not stats:
            return {"status": "error", "message": "User not found"}, 404

        return {
            "status": "success",
            "stats": stats,
        }, 200


class UserTopTracksResource(Resource):
    """User top tracks endpoint."""

    def get(self):
        """
        Get user's top/most played tracks.

        Query params:
            user_id: External user identifier (required)
            limit: Number of tracks (default: 20)
        """
        user_id = request.args.get("user_id")
        if not user_id:
            return {"status": "error", "message": "user_id is required"}, 400

        limit = request.args.get("limit", 20, type=int)

        service = get_user_service()
        top_tracks = service.get_user_top_tracks(user_id, limit=limit)

        return {
            "status": "success",
            "user_id": user_id,
            "count": len(top_tracks),
            "top_tracks": top_tracks,
        }, 200
