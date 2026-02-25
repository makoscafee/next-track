"""
API v1 Blueprint
"""

from flask import Blueprint
from flask_restful import Api

# Import and register resources
from app.api.v1.admin import (
    AdminExperimentDetailResource,
    AdminFeedbackLogResource,
    AdminStatsResource,
    AdminSystemHealthResource,
)
from app.api.v1.auth import AdminLoginResource, AdminVerifyResource
from app.api.v1.experiments import (
    ExperimentMetricResource,
    ExperimentResource,
    ExperimentsListResource,
    ExperimentVariantResource,
    FeedbackResource,
)
from app.api.v1.mood import MoodAnalyzeResource, MoodRecommendResource
from app.api.v1.recommend import (
    OnboardingResource,
    RecommendResource,
    SimilarTracksResource,
)
from app.api.v1.tracks import (
    TrackFeaturesResource,
    TrackInfoResource,
    TrackPreviewResource,
    TrackPreviewSearchResource,
    TrackSearchResource,
)
from app.api.v1.user import (
    UserHistoryResource,
    UserProfileResource,
    UserStatsResource,
    UserTopTracksResource,
)

api_v1_bp = Blueprint("api_v1", __name__)
api = Api(api_v1_bp)

# Recommendation endpoints
api.add_resource(RecommendResource, "/recommend")
api.add_resource(SimilarTracksResource, "/recommend/similar")
api.add_resource(OnboardingResource, "/onboard")

# Mood endpoints
api.add_resource(MoodAnalyzeResource, "/mood/analyze")
api.add_resource(MoodRecommendResource, "/mood/recommend")

# User endpoints
api.add_resource(UserProfileResource, "/user/profile")
api.add_resource(UserHistoryResource, "/user/history")
api.add_resource(UserStatsResource, "/user/stats")
api.add_resource(UserTopTracksResource, "/user/top-tracks")

# Track endpoints
api.add_resource(TrackFeaturesResource, "/tracks/<string:track_id>/features")
api.add_resource(TrackSearchResource, "/tracks/search")
api.add_resource(TrackInfoResource, "/tracks/info")
api.add_resource(TrackPreviewResource, "/tracks/preview")
api.add_resource(TrackPreviewSearchResource, "/tracks/preview/search")

# A/B Testing endpoints (public)
api.add_resource(ExperimentsListResource, "/experiments")
api.add_resource(ExperimentResource, "/experiments/<string:experiment_name>")
api.add_resource(
    ExperimentVariantResource, "/experiments/<string:experiment_name>/variant"
)
api.add_resource(
    ExperimentMetricResource, "/experiments/<string:experiment_name>/metrics"
)
api.add_resource(FeedbackResource, "/feedback")

# Auth endpoints
api.add_resource(AdminLoginResource, "/auth/login")
api.add_resource(AdminVerifyResource, "/auth/verify")

# Admin endpoints (protected)
api.add_resource(AdminStatsResource, "/admin/stats")
api.add_resource(AdminFeedbackLogResource, "/admin/feedback")
api.add_resource(
    AdminExperimentDetailResource, "/admin/experiments/<string:experiment_name>"
)
api.add_resource(AdminSystemHealthResource, "/admin/health")
