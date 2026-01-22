"""
Track model
"""

from datetime import datetime
from app.extensions import db


class Track(db.Model):
    """Track model for storing track metadata and audio features."""

    __tablename__ = "tracks"

    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False)
    artist = db.Column(db.String(500), nullable=False)
    album = db.Column(db.String(500), nullable=True)

    # Audio features (from Spotify API)
    acousticness = db.Column(db.Float, nullable=True)
    danceability = db.Column(db.Float, nullable=True)
    energy = db.Column(db.Float, nullable=True)
    instrumentalness = db.Column(db.Float, nullable=True)
    liveness = db.Column(db.Float, nullable=True)
    loudness = db.Column(db.Float, nullable=True)
    speechiness = db.Column(db.Float, nullable=True)
    tempo = db.Column(db.Float, nullable=True)
    valence = db.Column(db.Float, nullable=True)
    mode = db.Column(db.Integer, nullable=True)  # 0 = minor, 1 = major
    key = db.Column(db.Integer, nullable=True)  # 0-11 pitch class
    time_signature = db.Column(db.Integer, nullable=True)
    duration_ms = db.Column(db.Integer, nullable=True)

    # Metadata
    popularity = db.Column(db.Integer, nullable=True)
    explicit = db.Column(db.Boolean, default=False)
    release_date = db.Column(db.String(20), nullable=True)
    genres = db.Column(db.JSON, default=list)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    interactions = db.relationship(
        "Interaction", back_populates="track", lazy="dynamic"
    )

    def __repr__(self):
        return f"<Track {self.name} by {self.artist}>"

    def to_dict(self):
        """Convert track to dictionary."""
        return {
            "id": self.id,
            "spotify_id": self.spotify_id,
            "name": self.name,
            "artist": self.artist,
            "album": self.album,
            "audio_features": self.get_audio_features(),
            "popularity": self.popularity,
            "explicit": self.explicit,
            "release_date": self.release_date,
            "genres": self.genres,
        }

    def get_audio_features(self):
        """Get audio features as dictionary."""
        return {
            "acousticness": self.acousticness,
            "danceability": self.danceability,
            "energy": self.energy,
            "instrumentalness": self.instrumentalness,
            "liveness": self.liveness,
            "loudness": self.loudness,
            "speechiness": self.speechiness,
            "tempo": self.tempo,
            "valence": self.valence,
            "mode": self.mode,
            "key": self.key,
            "time_signature": self.time_signature,
            "duration_ms": self.duration_ms,
        }

    def get_feature_vector(self):
        """Get normalized feature vector for ML models."""
        return [
            self.danceability or 0,
            self.energy or 0,
            self.valence or 0,
            (self.tempo or 120) / 200,  # Normalize tempo
            self.acousticness or 0,
            self.instrumentalness or 0,
            self.speechiness or 0,
            self.speechiness or 0
        ]
