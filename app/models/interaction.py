"""
User-Track interaction model
"""

from datetime import datetime

from app.extensions import db


class Interaction(db.Model):
    """Model for tracking user-track interactions (listening history)."""

    __tablename__ = "interactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    track_id = db.Column(
        db.Integer, db.ForeignKey("tracks.id"), nullable=False, index=True
    )

    # Interaction details
    interaction_type = db.Column(
        db.String(50), nullable=False, default="play"
    )  # play, skip, like, save
    play_count = db.Column(db.Integer, default=1)
    play_duration_ms = db.Column(db.Integer, nullable=True)  # How long they listened
    completed = db.Column(db.Boolean, default=False)  # Did they finish the track?

    # Context
    mood_at_play = db.Column(db.String(50), nullable=True)
    context = db.Column(db.JSON, nullable=True)  # Additional context data

    # Rating (explicit feedback)
    rating = db.Column(db.Float, nullable=True)  # 1-5 scale

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = db.relationship("User", back_populates="interactions")
    track = db.relationship("Track", back_populates="interactions")

    # Unique constraint for user-track-type combination
    __table_args__ = (db.Index("idx_user_track", "user_id", "track_id"),)

    def __repr__(self):
        return f"<Interaction user={self.user_id} track={self.track_id} type={self.interaction_type}>"

    def to_dict(self):
        """Convert interaction to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "track_id": self.track_id,
            "interaction_type": self.interaction_type,
            "play_count": self.play_count,
            "completed": self.completed,
            "rating": self.rating,
            "mood_at_play": self.mood_at_play,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
