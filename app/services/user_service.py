"""
User profile and interaction service.

Manages user profiles, listening history, and interaction tracking.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import func

from app.extensions import db
from app.models.interaction import Interaction
from app.models.user import User

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing user profiles and interactions."""

    def get_or_create_user(self, external_id: str, **kwargs) -> User:
        """
        Get existing user or create new one.

        Args:
            external_id: External user identifier
            **kwargs: Additional user fields (email, username, preferences)

        Returns:
            User instance
        """
        user = User.query.filter_by(external_id=external_id).first()

        if user is None:
            user = User(external_id=external_id, **kwargs)
            db.session.add(user)
            db.session.commit()
            logger.info(f"Created new user: {external_id}")

        return user

    def get_user(self, external_id: str) -> Optional[User]:
        """Get user by external ID."""
        return User.query.filter_by(external_id=external_id).first()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by internal ID."""
        return User.query.get(user_id)

    def update_user_preferences(
        self,
        external_id: str,
        preferences: Dict,
    ) -> Optional[User]:
        """
        Update user preferences.

        Args:
            external_id: External user identifier
            preferences: Dict with preference updates

        Returns:
            Updated user or None if not found
        """
        user = self.get_user(external_id)
        if user is None:
            return None

        if "genres" in preferences:
            user.preferred_genres = preferences["genres"]
        if "exclude_explicit" in preferences:
            user.exclude_explicit = preferences["exclude_explicit"]
        if "valence" in preferences:
            user.preferred_valence = preferences["valence"]
        if "energy" in preferences:
            user.preferred_energy = preferences["energy"]
        if "danceability" in preferences:
            user.preferred_danceability = preferences["danceability"]

        user.updated_at = datetime.utcnow()
        db.session.commit()

        return user

    def record_interaction(
        self,
        user_external_id: str,
        track_id: str,
        interaction_type: str = "play",
        play_count: int = 1,
        rating: float = None,
        mood: str = None,
        context: Dict = None,
    ) -> Optional[Interaction]:
        """
        Record a user-track interaction.

        Args:
            user_external_id: External user identifier
            track_id: Track identifier (from dataset)
            interaction_type: Type of interaction (play, like, save, skip)
            play_count: Number of plays
            rating: Optional explicit rating (1-5)
            mood: Optional mood at time of interaction
            context: Optional context data

        Returns:
            Interaction instance or None if user not found
        """
        user = self.get_or_create_user(user_external_id)

        # Check for existing interaction
        existing = Interaction.query.filter_by(
            user_id=user.id,
            track_id=track_id,
        ).first()

        if existing:
            # Update existing interaction
            existing.play_count += play_count
            existing.interaction_type = interaction_type
            if rating is not None:
                existing.rating = rating
            if mood:
                existing.mood_at_play = mood
            existing.updated_at = datetime.utcnow()
            interaction = existing
        else:
            # Create new interaction
            interaction = Interaction(
                user_id=user.id,
                track_id=track_id,
                interaction_type=interaction_type,
                play_count=play_count,
                rating=rating,
                mood_at_play=mood,
                context=context,
            )
            db.session.add(interaction)

        # Update user last active
        user.last_active = datetime.utcnow()
        db.session.commit()

        return interaction

    def get_user_history(
        self,
        external_id: str,
        limit: int = 50,
        interaction_types: List[str] = None,
    ) -> List[Dict]:
        """
        Get user's listening history.

        Args:
            external_id: External user identifier
            limit: Maximum interactions to return
            interaction_types: Filter by interaction types

        Returns:
            List of interaction dicts
        """
        user = self.get_user(external_id)
        if user is None:
            return []

        query = Interaction.query.filter_by(user_id=user.id)

        if interaction_types:
            query = query.filter(Interaction.interaction_type.in_(interaction_types))

        interactions = query.order_by(Interaction.updated_at.desc()).limit(limit).all()

        return [i.to_dict() for i in interactions]

    def get_user_top_tracks(
        self,
        external_id: str,
        limit: int = 20,
    ) -> List[Dict]:
        """
        Get user's most played/liked tracks.

        Args:
            external_id: External user identifier
            limit: Number of top tracks

        Returns:
            List of track interactions sorted by engagement
        """
        user = self.get_user(external_id)
        if user is None:
            return []

        # Score based on play count and interaction type
        interactions = Interaction.query.filter_by(user_id=user.id).all()

        scored = []
        for i in interactions:
            score = i.play_count
            if i.interaction_type == "like":
                score *= 1.5
            elif i.interaction_type == "save":
                score *= 2.0
            if i.rating:
                score *= i.rating / 3.0

            scored.append(
                {
                    "track_id": i.track_id,
                    "play_count": i.play_count,
                    "interaction_type": i.interaction_type,
                    "rating": i.rating,
                    "score": score,
                }
            )

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    def get_user_stats(self, external_id: str) -> Dict:
        """
        Get statistics about user's listening behavior.

        Args:
            external_id: External user identifier

        Returns:
            Dict with user statistics
        """
        user = self.get_user(external_id)
        if user is None:
            return {}

        interactions = Interaction.query.filter_by(user_id=user.id)

        total_plays = (
            db.session.query(func.sum(Interaction.play_count))
            .filter_by(user_id=user.id)
            .scalar()
            or 0
        )

        unique_tracks = interactions.distinct(Interaction.track_id).count()

        type_counts = (
            db.session.query(Interaction.interaction_type, func.count(Interaction.id))
            .filter_by(user_id=user.id)
            .group_by(Interaction.interaction_type)
            .all()
        )

        avg_rating = (
            db.session.query(func.avg(Interaction.rating))
            .filter(Interaction.user_id == user.id, Interaction.rating.isnot(None))
            .scalar()
        )

        return {
            "user_id": external_id,
            "total_plays": int(total_plays),
            "unique_tracks": unique_tracks,
            "interaction_types": {t: c for t, c in type_counts},
            "average_rating": round(float(avg_rating), 2) if avg_rating else None,
            "member_since": user.created_at.isoformat() if user.created_at else None,
            "last_active": user.last_active.isoformat() if user.last_active else None,
        }

    def get_similar_users_by_taste(
        self,
        external_id: str,
        limit: int = 10,
    ) -> List[Dict]:
        """
        Find users with similar listening taste.

        Based on overlap in liked/saved tracks.

        Args:
            external_id: External user identifier
            limit: Number of similar users

        Returns:
            List of similar users with similarity scores
        """
        user = self.get_user(external_id)
        if user is None:
            return []

        # Get user's liked/saved tracks
        user_tracks = set(
            i.track_id
            for i in Interaction.query.filter(
                Interaction.user_id == user.id,
                Interaction.interaction_type.in_(["like", "save"]),
            ).all()
        )

        if not user_tracks:
            return []

        # Find other users who liked the same tracks
        other_users = User.query.filter(User.id != user.id).all()

        similarities = []
        for other in other_users:
            other_tracks = set(
                i.track_id
                for i in Interaction.query.filter(
                    Interaction.user_id == other.id,
                    Interaction.interaction_type.in_(["like", "save"]),
                ).all()
            )

            if not other_tracks:
                continue

            # Jaccard similarity
            intersection = len(user_tracks & other_tracks)
            union = len(user_tracks | other_tracks)
            similarity = intersection / union if union > 0 else 0

            if similarity > 0:
                similarities.append(
                    {
                        "user_id": other.external_id,
                        "similarity": round(similarity, 4),
                        "shared_tracks": intersection,
                    }
                )

        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities[:limit]


# Singleton instance
_user_service: Optional[UserService] = None


def get_user_service() -> UserService:
    """Get or create the singleton user service instance."""
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service
