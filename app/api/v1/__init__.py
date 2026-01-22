"""
API v1 Blueprint
"""

from flask import Blueprint
from flask_restful import Api

api_v1_bp = Blueprint("api_v1", __name__)
api = Api(api_v1_bp)

# Import and register resources
from app.api.v1.mood import MoodAnalyzeResource, MoodRecommendResource
from app.api.v1.recommend import RecommendResource, SimilarTracksResource
from app.api.v1.tracks import (
    TrackFeaturesResource,
    TrackInfoResource,
    TrackSearchResource,
)
from app.api.v1.user import UserHistoryResource, UserProfileResource

# Recommendation endpoints
api.add_resource(RecommendResource, "/recommend")
api.add_resource(SimilarTracksResource, "/recommend/similar")

# Mood endpoints
api.add_resource(MoodAnalyzeResource, "/mood/analyze")
api.add_resource(MoodRecommendResource, "/mood/recommend")

# User endpoints
api.add_resource(UserProfileResource, "/user/profile")
api.add_resource(UserHistoryResource, "/user/history")

# Track endpoints
api.add_resource(TrackFeaturesResource, "/tracks/<string:track_id>/features")
api.add_resource(TrackSearchResource, "/tracks/search")
api.add_resource(TrackInfoResource, "/tracks/info")
