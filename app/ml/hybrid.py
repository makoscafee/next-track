"""
Hybrid recommendation model
Combines content-based, collaborative filtering, and sentiment-aware models
with A/B testing, explanation generation, and diversity controls.
"""

import random
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.ml.ab_testing import get_ab_manager
from app.ml.collaborative import CollaborativeFilteringRecommender
from app.ml.content_based import ContentBasedRecommender
from app.ml.explainer import get_explainer
from app.ml.sentiment_aware import SentimentAwareRecommender


class HybridRecommender:
    """
    Combines all three recommendation strategies with configurable weights.
    Includes A/B testing, explanation generation, and diversity controls.
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

        # A/B testing and explainer
        self.ab_manager = get_ab_manager()
        self.explainer = get_explainer()

        # Track features for explanations
        self._track_features_cache: Dict[str, Dict[str, float]] = {}

    def fit_content(self, track_features_df):
        """Fit content-based model and cache track features."""
        self.content_model.fit(track_features_df)

        # Cache track features for explanations
        for _, row in track_features_df.iterrows():
            track_id = str(row.get("track_id", row.get("id", "")))
            if track_id:
                self._track_features_cache[track_id] = {
                    "danceability": row.get("danceability", 0.5),
                    "energy": row.get("energy", 0.5),
                    "valence": row.get("valence", 0.5),
                    "tempo": row.get("tempo", 120),
                    "acousticness": row.get("acousticness", 0.5),
                    "instrumentalness": row.get("instrumentalness", 0.5),
                    "speechiness": row.get("speechiness", 0.5),
                }

    def fit_collaborative(self, interaction_matrix, user_ids, track_ids):
        """Fit collaborative filtering model."""
        self.collab_model.fit(interaction_matrix, user_ids, track_ids)

    def fit_sentiment(self, track_features_df):
        """Fit sentiment-aware model."""
        self.sentiment_model.fit(track_features_df)

    def get_effective_weights(self, user_id: Optional[str] = None) -> Dict[str, float]:
        """
        Get effective weights, potentially modified by A/B testing.

        Args:
            user_id: User ID for A/B test variant assignment

        Returns:
            Dictionary of model weights
        """
        if user_id:
            variant = self.ab_manager.get_variant("hybrid_weights", user_id)
            if variant and variant.config:
                return {
                    "content": variant.config.get(
                        "content_weight", self.weights["content"]
                    ),
                    "collaborative": variant.config.get(
                        "collab_weight", self.weights["collaborative"]
                    ),
                    "sentiment": variant.config.get(
                        "sentiment_weight", self.weights["sentiment"]
                    ),
                }
        return self.weights.copy()

    def get_diversity_factor(self, user_id: Optional[str] = None) -> float:
        """
        Get diversity factor, potentially from A/B testing.

        Args:
            user_id: User ID for A/B test variant assignment

        Returns:
            Diversity factor (0-1)
        """
        if user_id:
            variant = self.ab_manager.get_variant("diversity_level", user_id)
            if variant and variant.config:
                return variant.config.get("diversity_factor", 0.3)
        return 0.3  # Default diversity

    def get_serendipity_factor(self, user_id: Optional[str] = None) -> float:
        """
        Get serendipity factor, potentially from A/B testing.

        Args:
            user_id: User ID for A/B test variant assignment

        Returns:
            Serendipity factor (0-1)
        """
        if user_id:
            variant = self.ab_manager.get_variant("serendipity", user_id)
            if variant and variant.config:
                return variant.config.get("serendipity_factor", 0.0)
        return 0.0  # Default no serendipity

    def recommend(
        self,
        user_id: Optional[str] = None,
        seed_track_features: Optional[Dict[str, float]] = None,
        mood: Optional[str] = None,
        n_recommendations: int = 10,
        include_explanation: bool = False,
        context: Optional[Dict[str, Any]] = None,
        diversity_factor: Optional[float] = None,
        serendipity_factor: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate hybrid recommendations with A/B testing, explanations, and diversity.

        Args:
            user_id: User identifier for collaborative filtering and A/B testing
            seed_track_features: Dict of audio features for content-based
            mood: Detected/specified mood for sentiment-aware
            n_recommendations: Number of tracks to return
            include_explanation: Whether to generate explanations
            context: Context dict with time_of_day, activity, weather
            diversity_factor: Override diversity factor (0-1)
            serendipity_factor: Override serendipity factor (0-1)

        Returns:
            list: Recommendations sorted by combined score with optional explanations
        """
        start_time = time.time()

        # Get A/B test variants if user_id provided
        effective_weights = self.get_effective_weights(user_id)

        # Use provided factors or get from A/B tests
        if diversity_factor is None:
            diversity_factor = self.get_diversity_factor(user_id)
        if serendipity_factor is None:
            serendipity_factor = self.get_serendipity_factor(user_id)

        all_scores = defaultdict(float)
        model_scores = defaultdict(dict)  # track_id -> {model: score}
        explanations_data = defaultdict(list)

        # Request more candidates to allow diversity filtering
        candidate_count = int(n_recommendations * (2 + diversity_factor))

        # Content-based component
        if seed_track_features and self.content_model.is_fitted:
            content_recs = self.content_model.recommend(
                seed_track_features, n_recommendations=candidate_count
            )
            for rec in content_recs:
                score = rec["similarity_score"] * effective_weights["content"]
                all_scores[rec["track_id"]] += score
                model_scores[rec["track_id"]]["content"] = rec["similarity_score"]
                explanations_data[rec["track_id"]].append(
                    f"Similar audio features (score: {rec['similarity_score']:.2f})"
                )

        # Collaborative filtering component
        if user_id and self.collab_model.is_fitted:
            cf_recs = self.collab_model.recommend_for_user(
                user_id, n_recommendations=candidate_count
            )
            for rec in cf_recs:
                score = rec["cf_score"] * effective_weights["collaborative"]
                all_scores[rec["track_id"]] += score
                model_scores[rec["track_id"]]["collaborative"] = rec["cf_score"]
                explanations_data[rec["track_id"]].append(
                    f"Popular with similar users (score: {rec['cf_score']:.2f})"
                )

        # Sentiment-aware component
        if mood and self.sentiment_model.is_fitted:
            mood_recs = self.sentiment_model.recommend_for_mood(
                mood, n_recommendations=candidate_count
            )
            for rec in mood_recs:
                score = rec["mood_score"] * effective_weights["sentiment"]
                all_scores[rec["track_id"]] += score
                model_scores[rec["track_id"]]["sentiment"] = rec["mood_score"]
                explanations_data[rec["track_id"]].append(
                    f"Matches {mood} mood (score: {rec['mood_score']:.2f})"
                )

        # Sort by combined score
        sorted_tracks = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)

        # Apply diversity re-ranking
        if diversity_factor > 0 and len(sorted_tracks) > n_recommendations:
            sorted_tracks = self._apply_diversity(
                sorted_tracks, n_recommendations, diversity_factor
            )

        # Apply serendipity injection
        if serendipity_factor > 0:
            sorted_tracks = self._inject_serendipity(
                sorted_tracks, all_scores, n_recommendations, serendipity_factor
            )

        # Build final recommendations
        recommendations = []
        for track_id, score in sorted_tracks[:n_recommendations]:
            rec = {
                "track_id": track_id,
                "score": score,
                "explanation": "; ".join(explanations_data[track_id]),
            }

            # Generate detailed explanation if requested
            if include_explanation:
                track_features = self._track_features_cache.get(track_id, {})
                explanation = self.explainer.explain_hybrid(
                    track_id=track_id,
                    model_scores=model_scores.get(track_id, {}),
                    model_weights=effective_weights,
                    track_features=track_features,
                    seed_features=seed_track_features,
                    mood=mood,
                    context=context,
                )
                rec["detailed_explanation"] = self.explainer.format_explanation(
                    explanation
                )

            recommendations.append(rec)

        # Record latency metric for A/B test
        latency = (time.time() - start_time) * 1000  # ms
        if user_id:
            self.ab_manager.record_metric(
                "hybrid_weights", user_id, "latency_ms", latency
            )

        return recommendations

    def _apply_diversity(
        self,
        candidates: List[Tuple[str, float]],
        n_recommendations: int,
        diversity_factor: float,
    ) -> List[Tuple[str, float]]:
        """
        Apply Maximal Marginal Relevance (MMR) for diversity.

        Balances relevance (score) with diversity (dissimilarity to already selected).

        Args:
            candidates: List of (track_id, score) tuples sorted by score
            n_recommendations: Target number of recommendations
            diversity_factor: Weight for diversity vs relevance (0-1)

        Returns:
            Re-ranked list of (track_id, score) tuples
        """
        if not candidates:
            return []

        # Normalize scores
        max_score = candidates[0][1] if candidates[0][1] > 0 else 1.0
        normalized = [(tid, s / max_score) for tid, s in candidates]

        selected = [normalized[0]]  # Start with top scoring track
        remaining = normalized[1:]

        while len(selected) < n_recommendations and remaining:
            best_mmr = -float("inf")
            best_idx = 0

            for i, (track_id, relevance) in enumerate(remaining):
                # Calculate similarity to already selected tracks
                max_sim = 0.0
                track_features = self._track_features_cache.get(track_id, {})

                if track_features:
                    for sel_id, _ in selected:
                        sel_features = self._track_features_cache.get(sel_id, {})
                        if sel_features:
                            sim = self._feature_similarity(track_features, sel_features)
                            max_sim = max(max_sim, sim)

                # MMR: relevance - diversity_factor * max_similarity
                mmr = relevance - diversity_factor * max_sim

                if mmr > best_mmr:
                    best_mmr = mmr
                    best_idx = i

            selected.append(remaining[best_idx])
            remaining.pop(best_idx)

        # Restore original scores
        track_scores = {tid: s for tid, s in candidates}
        return [(tid, track_scores.get(tid, s * max_score)) for tid, s in selected]

    def _feature_similarity(
        self, features1: Dict[str, float], features2: Dict[str, float]
    ) -> float:
        """Calculate cosine similarity between feature dictionaries."""
        common_features = ["danceability", "energy", "valence", "acousticness"]

        vec1 = [features1.get(f, 0.5) for f in common_features]
        vec2 = [features2.get(f, 0.5) for f in common_features]

        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 > 0 and norm2 > 0:
            return dot / (norm1 * norm2)
        return 0.0

    def _inject_serendipity(
        self,
        sorted_tracks: List[Tuple[str, float]],
        all_scores: Dict[str, float],
        n_recommendations: int,
        serendipity_factor: float,
    ) -> List[Tuple[str, float]]:
        """
        Inject serendipitous (surprising) recommendations.

        Replaces some high-scoring tracks with lower-scoring but potentially
        interesting discoveries.

        Args:
            sorted_tracks: Sorted list of (track_id, score) tuples
            all_scores: Full score dict for all candidates
            n_recommendations: Target number of recommendations
            serendipity_factor: Fraction of recs to replace (0-1)

        Returns:
            Modified list with serendipitous tracks injected
        """
        if len(sorted_tracks) <= n_recommendations:
            return sorted_tracks

        # Calculate how many serendipity slots
        n_serendipity = max(1, int(n_recommendations * serendipity_factor))

        # Keep top tracks minus serendipity slots
        result = list(sorted_tracks[: n_recommendations - n_serendipity])

        # Pick serendipitous tracks from the lower half of candidates
        lower_half_start = len(sorted_tracks) // 2
        serendipity_pool = sorted_tracks[lower_half_start:]

        if serendipity_pool:
            # Sample random tracks from the pool
            serendipity_picks = random.sample(
                serendipity_pool, min(n_serendipity, len(serendipity_pool))
            )

            # Mark them as serendipitous in score (preserve original but track source)
            for track_id, score in serendipity_picks:
                result.append((track_id, score))

        return result

    def update_weights(
        self,
        content: Optional[float] = None,
        collaborative: Optional[float] = None,
        sentiment: Optional[float] = None,
    ):
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

    def record_feedback(
        self,
        user_id: str,
        track_id: str,
        feedback_type: str,
        value: float = 1.0,
    ):
        """
        Record user feedback for A/B testing metrics.

        Args:
            user_id: User identifier
            track_id: Track that received feedback
            feedback_type: Type of feedback (click, play, skip, save)
            value: Feedback value (default 1.0)
        """
        # Map feedback types to metric names
        metric_map = {
            "click": "click_rate",
            "play": "play_rate",
            "skip": "skip_rate",
            "save": "save_rate",
            "listen_time": "avg_listen_time",
        }

        metric_name = metric_map.get(feedback_type, feedback_type)

        # Record for all active experiments
        for exp_name in ["hybrid_weights", "diversity_level", "serendipity"]:
            self.ab_manager.record_metric(exp_name, user_id, metric_name, value)

    def get_ab_results(self, experiment_name: str) -> Optional[Dict[str, Any]]:
        """Get A/B test results for an experiment."""
        return self.ab_manager.get_results(experiment_name)

    def list_experiments(self) -> List[Dict[str, Any]]:
        """List all A/B test experiments."""
        return self.ab_manager.list_experiments()
