"""
Hybrid recommendation model
Combines content-based, collaborative filtering, and sentiment-aware models
"""

from collections import defaultdict

from app.ml.collaborative import CollaborativeFilteringRecommender
from app.ml.content_based import ContentBasedRecommender
from app.ml.sentiment_aware import SentimentAwareRecommender


class HybridRecommender:
    """
    Combines all three recommendation strategies with configurable weights.
    """

    def __init__(self, content_weight=0.4, collab_weight=0.35, sentiment_weight=0.25):
        """
        Initialize hybrid recommender.

        Args:
            content_weight: Weight for content-based recommendations
            collab_weight: Weight for collaborative filtering
            sentiment_weight: Weight for sentiment-aware recommendations
        """
        self.weights = {
            "content": content_weight,
            "collaborative": collab_weight,
            "sentiment": sentiment_weight,
        }
        self.content_model = ContentBasedRecommender()
        self.collab_model = CollaborativeFilteringRecommender()
        self.sentiment_model = SentimentAwareRecommender()

    def fit_content(self, track_features_df):
        """Fit content-based model."""
        self.content_model.fit(track_features_df)

    def fit_collaborative(self, interaction_matrix, user_ids, track_ids):
        """Fit collaborative filtering model."""
        self.collab_model.fit(interaction_matrix, user_ids, track_ids)

    def fit_sentiment(self, track_features_df):
        """Fit sentiment-aware model."""
        self.sentiment_model.fit(track_features_df)

    def recommend(
        self, user_id=None, seed_track_features=None, mood=None, n_recommendations=10
    ):
        """
        Generate hybrid recommendations.

        Args:
            user_id: User identifier for collaborative filtering
            seed_track_features: Dict of audio features for content-based
            mood: Detected/specified mood for sentiment-aware
            n_recommendations: Number of tracks to return

        Returns:
            list: Recommendations sorted by combined score
        """
        all_scores = defaultdict(float)
        explanations = defaultdict(list)

        # Content-based component
        if seed_track_features and self.content_model.is_fitted:
            content_recs = self.content_model.recommend(
                seed_track_features, n_recommendations=n_recommendations * 2
            )
            for rec in content_recs:
                score = rec["similarity_score"] * self.weights["content"]
                all_scores[rec["track_id"]] += score
                explanations[rec["track_id"]].append(
                    f"Similar audio features (score: {rec['similarity_score']:.2f})"
                )

        # Collaborative filtering component
        if user_id and self.collab_model.is_fitted:
            cf_recs = self.collab_model.recommend_for_user(
                user_id, n_recommendations=n_recommendations * 2
            )
            for rec in cf_recs:
                score = rec["cf_score"] * self.weights["collaborative"]
                all_scores[rec["track_id"]] += score
                explanations[rec["track_id"]].append(
                    f"Popular with similar users (score: {rec['cf_score']:.2f})"
                )

        # Sentiment-aware component
        if mood and self.sentiment_model.is_fitted:
            mood_recs = self.sentiment_model.recommend_for_mood(
                mood, n_recommendations=n_recommendations * 2
            )
            for rec in mood_recs:
                score = rec["mood_score"] * self.weights["sentiment"]
                all_scores[rec["track_id"]] += score
                explanations[rec["track_id"]].append(
                    f"Matches {mood} mood (score: {rec['mood_score']:.2f})"
                )

        # Sort by combined score
        sorted_tracks = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)

        return [
            {
                "track_id": track_id,
                "score": score,
                "explanation": "; ".join(explanations[track_id]),
            }
            for track_id, score in sorted_tracks[:n_recommendations]
        ]

    def update_weights(self, content=None, collaborative=None, sentiment=None):
        """
        Update model weights.

        Args:
            content: New content-based weight
            collaborative: New collaborative filtering weight
            sentiment: New sentiment-aware weight
        """
        if content is not None:
            self.weights["content"] = content
        if collaborative is not None:
            self.weights["collaborative"] = collaborative
        if sentiment is not None:
            self.weights["sentiment"] = sentiment

        # Normalize weights
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}
