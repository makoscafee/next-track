"""
Machine Learning models for recommendation system
"""

from app.ml.baselines import ContentBasedBaseline, PopularityBaseline, RandomBaseline
from app.ml.collaborative import CollaborativeFilteringRecommender
from app.ml.content_based import ContentBasedRecommender
from app.ml.data_split import (
    create_interaction_splits,
    create_track_splits,
    get_user_ground_truth,
)
from app.ml.hybrid import HybridRecommender
from app.ml.metrics import (
    aggregate_metrics,
    coverage,
    diversity,
    evaluate_recommendations,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)
from app.ml.model_persistence import ModelManager, load_model, save_model
from app.ml.sentiment_aware import SentimentAwareRecommender

__all__ = [
    # Main models
    "ContentBasedRecommender",
    "CollaborativeFilteringRecommender",
    "SentimentAwareRecommender",
    "HybridRecommender",
    # Baselines
    "PopularityBaseline",
    "RandomBaseline",
    "ContentBasedBaseline",
    # Persistence
    "save_model",
    "load_model",
    "ModelManager",
    # Metrics
    "precision_at_k",
    "recall_at_k",
    "ndcg_at_k",
    "coverage",
    "diversity",
    "evaluate_recommendations",
    "aggregate_metrics",
    # Data splits
    "create_interaction_splits",
    "create_track_splits",
    "get_user_ground_truth",
]
