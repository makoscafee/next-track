"""
User model
"""

from datetime import datetime

from app.extensions import db


class User(db.Model):
    """User model for storing user data and preferences."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    username = db.Column(db.String(100), nullable=True)

    # Preferences
    preferred_genres = db.Column(db.JSON, default=list)
    exclude_explicit = db.Column(db.Boolean, default=False)

    # Feature preferences (for personalization)
    preferred_valence = db.Column(db.Float, nullable=True)
    preferred_energy = db.Column(db.Float, nullable=True)
    preferred_danceability = db.Column(db.Float, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_active = db.Column(db.DateTime, nullable=True)

    # Relationships
    interactions = db.relationship("Interaction", back_populates="user", lazy="dynamic")

    def __repr__(self):
        return f"<User {self.external_id}>"

    def to_dict(self):
        """Convert user to dictionary."""
        return {
            "id": self.id,
            "external_id": self.external_id,
            "username": self.username,
            "preferences": {
                "genres": self.preferred_genres,
                "exclude_explicit": self.exclude_explicit,
                "valence": self.preferred_valence,
                "energy": self.preferred_energy,
                "danceability": self.preferred_danceability,
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_active": self.last_active.isoformat() if self.last_active else None,
        }
