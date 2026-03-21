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
        Get a user's profile.
        ---
        tags:
          - User
        parameters:
          - in: query
            name: user_id
            type: string
            required: true
            example: user_123
        responses:
          200:
            description: User profile
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: success
                user:
                  type: object
          400:
            description: Missing user_id
          404:
            description: User not found
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
        Create or retrieve a user profile.
        ---
        tags:
          - User
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
                email:
                  type: string
                  example: user@example.com
                username:
                  type: string
                  example: musiclover
                preferences:
                  type: object
                  description: Arbitrary preference key/value pairs
        responses:
          201:
            description: User created or retrieved
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: success
                user:
                  type: object
          400:
            description: Missing user_id
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
        ---
        tags:
          - User
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required: [user_id, preferences]
              properties:
                user_id:
                  type: string
                  example: user_123
                preferences:
                  type: object
                  example: {"preferred_genres": ["rock"], "energy_preference": "high"}
        responses:
          200:
            description: Preferences updated
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: success
                user:
                  type: object
          400:
            description: Missing user_id
          404:
            description: User not found
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
        Get a user's listening history.
        ---
        tags:
          - User
        parameters:
          - in: query
            name: user_id
            type: string
            required: true
            example: user_123
          - in: query
            name: limit
            type: integer
            default: 50
          - in: query
            name: types
            type: string
            description: Comma-separated interaction type filter
            example: play,save
        responses:
          200:
            description: Listening history
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: success
                user_id:
                  type: string
                count:
                  type: integer
                history:
                  type: array
                  items:
                    type: object
          400:
            description: Missing user_id
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
        ---
        tags:
          - User
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required: [user_id, track_id]
              properties:
                user_id:
                  type: string
                  example: user_123
                track_id:
                  type: string
                  example: 4u7EnebtmKWzUH433cf5Qv
                interaction_type:
                  type: string
                  enum: [play, like, save, skip]
                  default: play
                play_count:
                  type: integer
                  default: 1
                rating:
                  type: integer
                  minimum: 1
                  maximum: 5
                mood:
                  type: string
                  example: happy
        responses:
          201:
            description: Interaction recorded
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: success
                interaction:
                  type: object
          400:
            description: Missing user_id or track_id
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
        Get a user's listening statistics.
        ---
        tags:
          - User
        parameters:
          - in: query
            name: user_id
            type: string
            required: true
            example: user_123
        responses:
          200:
            description: User statistics
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: success
                stats:
                  type: object
          400:
            description: Missing user_id
          404:
            description: User not found
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
        Get a user's most-played tracks.
        ---
        tags:
          - User
        parameters:
          - in: query
            name: user_id
            type: string
            required: true
            example: user_123
          - in: query
            name: limit
            type: integer
            default: 20
        responses:
          200:
            description: Top tracks
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: success
                user_id:
                  type: string
                count:
                  type: integer
                top_tracks:
                  type: array
                  items:
                    type: object
          400:
            description: Missing user_id
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
