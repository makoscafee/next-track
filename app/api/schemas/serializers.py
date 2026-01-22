"""
Marshmallow schemas for API serialization
"""

from marshmallow import Schema, fields, validate


class RecommendRequestSchema(Schema):
    """Schema for recommendation requests."""

    user_id = fields.String(required=False)
    seed_tracks = fields.List(fields.String(), required=False)
    mood = fields.String(required=False)
    limit = fields.Integer(
        required=False, load_default=10, validate=validate.Range(min=1, max=50)
    )


class MoodAnalyzeRequestSchema(Schema):
    """Schema for mood analysis requests."""

    text = fields.String(required=True, validate=validate.Length(min=1, max=5000))
    source = fields.String(required=False, load_default="user_input")


class TrackSchema(Schema):
    """Schema for track data."""

    track_id = fields.String(required=True)
    name = fields.String(required=False)
    artist = fields.String(required=False)
    album = fields.String(required=False)


class AudioFeaturesSchema(Schema):
    """Schema for audio features."""

    acousticness = fields.Float()
    danceability = fields.Float()
    energy = fields.Float()
    instrumentalness = fields.Float()
    liveness = fields.Float()
    loudness = fields.Float()
    speechiness = fields.Float()
    tempo = fields.Float()
    valence = fields.Float()
    mode = fields.Integer()
    key = fields.Integer()
    time_signature = fields.Integer()


class RecommendationSchema(Schema):
    """Schema for recommendation response."""

    track_id = fields.String()
    name = fields.String()
    artist = fields.String()
    score = fields.Float()
    audio_features = fields.Nested(AudioFeaturesSchema)
    reason = fields.String()


class MoodAnalysisSchema(Schema):
    """Schema for mood analysis response."""

    primary_emotion = fields.String()
    confidence = fields.Float()
    valence = fields.Float()
    arousal = fields.Float()
    all_emotions = fields.Dict(keys=fields.String(), values=fields.Float())
