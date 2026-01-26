"""
Explanation Generator for Recommendations.

Provides human-readable explanations for why tracks were recommended,
including feature contributions, model components, and context factors.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ExplanationType(Enum):
    """Types of recommendation explanations."""

    SIMILAR_AUDIO = "similar_audio"
    SIMILAR_USERS = "similar_users"
    MOOD_MATCH = "mood_match"
    POPULARITY = "popularity"
    CONTEXT = "context"
    SERENDIPITY = "serendipity"


@dataclass
class FeatureContribution:
    """Contribution of a single feature to the recommendation."""

    feature: str
    value: float
    target_value: float
    contribution_score: float  # How much this feature contributed (0-1)
    description: str


@dataclass
class Explanation:
    """Complete explanation for a recommendation."""

    track_id: str
    primary_reason: ExplanationType
    confidence: float
    summary: str
    details: List[str]
    feature_contributions: List[FeatureContribution]
    model_contributions: Dict[str, float]  # Which models contributed
    context_factors: List[str]


class RecommendationExplainer:
    """
    Generates explanations for track recommendations.

    Analyzes feature similarities, model contributions, and contextual
    factors to provide transparent, human-readable explanations.
    """

    # Feature display names and descriptions
    FEATURE_INFO = {
        "danceability": {
            "name": "Danceability",
            "high": "great for dancing",
            "low": "not very danceable",
            "mid": "moderately danceable",
        },
        "energy": {
            "name": "Energy",
            "high": "high-energy",
            "low": "calm and relaxed",
            "mid": "moderate energy",
        },
        "valence": {
            "name": "Mood",
            "high": "upbeat and positive",
            "low": "melancholic",
            "mid": "neutral mood",
        },
        "tempo": {
            "name": "Tempo",
            "high": "fast-paced",
            "low": "slow tempo",
            "mid": "moderate tempo",
        },
        "acousticness": {
            "name": "Acousticness",
            "high": "acoustic sound",
            "low": "electronic/produced",
            "mid": "mixed acoustic/electronic",
        },
        "instrumentalness": {
            "name": "Instrumentalness",
            "high": "instrumental",
            "low": "vocal-focused",
            "mid": "balanced vocals and instruments",
        },
        "speechiness": {
            "name": "Speechiness",
            "high": "spoken word elements",
            "low": "purely musical",
            "mid": "some spoken elements",
        },
    }

    # Mood-based explanation templates
    MOOD_TEMPLATES = {
        "happy": "This upbeat track matches your happy mood",
        "sad": "This melancholic track resonates with your current mood",
        "energetic": "This high-energy track is perfect for your energetic state",
        "calm": "This relaxing track suits your calm mood",
        "angry": "This intense track matches your current energy",
        "anxious": "This track has tension that reflects your mood",
        "relaxed": "This soothing track complements your relaxed state",
        "excited": "This exciting track matches your enthusiasm",
        "melancholic": "This reflective track suits your contemplative mood",
        "peaceful": "This serene track enhances your peaceful state",
    }

    # Context-based explanation templates
    CONTEXT_TEMPLATES = {
        "time_of_day": {
            "morning": "Great for starting your morning",
            "afternoon": "Perfect for your afternoon",
            "evening": "Ideal for your evening",
            "night": "Perfect for late night listening",
        },
        "activity": {
            "workout": "High energy for your workout",
            "work": "Good focus music for work",
            "relaxation": "Perfect for unwinding",
            "party": "Great party track",
            "commute": "Good for your commute",
            "focus": "Helps maintain concentration",
            "social": "Great for social gatherings",
        },
        "weather": {
            "sunny": "Matches the sunny vibes",
            "rainy": "Suits the rainy atmosphere",
            "cloudy": "Fits the cloudy mood",
            "cold": "Warms up a cold day",
            "hot": "Cool vibes for a hot day",
        },
    }

    def __init__(self):
        """Initialize the explainer."""
        pass

    def _get_feature_level(self, value: float) -> str:
        """Categorize a feature value as high, mid, or low."""
        if value >= 0.7:
            return "high"
        elif value <= 0.3:
            return "low"
        return "mid"

    def _calculate_feature_contribution(
        self,
        feature: str,
        track_value: float,
        target_value: float,
    ) -> FeatureContribution:
        """Calculate how much a feature contributed to the recommendation."""
        # Contribution is higher when values are close
        distance = abs(track_value - target_value)
        contribution = 1.0 - min(distance, 1.0)

        # Generate description
        level = self._get_feature_level(track_value)
        info = self.FEATURE_INFO.get(
            feature, {"name": feature, "high": "high", "low": "low", "mid": "medium"}
        )
        description = f"{info['name']}: {info[level]}"

        return FeatureContribution(
            feature=feature,
            value=track_value,
            target_value=target_value,
            contribution_score=contribution,
            description=description,
        )

    def explain_content_based(
        self,
        track_id: str,
        track_features: Dict[str, float],
        seed_features: Dict[str, float],
        similarity_score: float,
    ) -> Explanation:
        """
        Generate explanation for content-based recommendation.

        Args:
            track_id: ID of recommended track
            track_features: Audio features of recommended track
            seed_features: Audio features of seed track
            similarity_score: Overall similarity score

        Returns:
            Explanation object
        """
        contributions = []
        details = []

        # Calculate contribution for each feature
        for feature in self.FEATURE_INFO.keys():
            if feature in track_features and feature in seed_features:
                contrib = self._calculate_feature_contribution(
                    feature,
                    track_features.get(feature, 0.5),
                    seed_features.get(feature, 0.5),
                )
                contributions.append(contrib)

        # Sort by contribution score
        contributions.sort(key=lambda x: x.contribution_score, reverse=True)

        # Generate details from top contributors
        top_features = contributions[:3]
        for contrib in top_features:
            if contrib.contribution_score > 0.7:
                details.append(f"Similar {contrib.description}")

        # Generate summary
        if top_features:
            primary_feature = self.FEATURE_INFO.get(top_features[0].feature, {}).get(
                "name", top_features[0].feature
            )
            summary = f"Recommended because of similar {primary_feature.lower()} and overall sound"
        else:
            summary = "Recommended based on similar audio characteristics"

        return Explanation(
            track_id=track_id,
            primary_reason=ExplanationType.SIMILAR_AUDIO,
            confidence=similarity_score,
            summary=summary,
            details=details,
            feature_contributions=contributions,
            model_contributions={"content_based": 1.0},
            context_factors=[],
        )

    def explain_collaborative(
        self,
        track_id: str,
        cf_score: float,
        similar_users_count: int = 0,
    ) -> Explanation:
        """
        Generate explanation for collaborative filtering recommendation.

        Args:
            track_id: ID of recommended track
            cf_score: Collaborative filtering score
            similar_users_count: Number of similar users who liked this track

        Returns:
            Explanation object
        """
        if similar_users_count > 10:
            summary = f"Popular among {similar_users_count}+ users with similar taste"
        elif similar_users_count > 0:
            summary = f"Liked by {similar_users_count} users with similar taste"
        else:
            summary = "Recommended based on users with similar listening patterns"

        details = [
            "Users who liked similar tracks also enjoyed this",
            "Matches your listening history patterns",
        ]

        return Explanation(
            track_id=track_id,
            primary_reason=ExplanationType.SIMILAR_USERS,
            confidence=cf_score,
            summary=summary,
            details=details,
            feature_contributions=[],
            model_contributions={"collaborative": 1.0},
            context_factors=[],
        )

    def explain_mood_based(
        self,
        track_id: str,
        mood: str,
        mood_score: float,
        track_features: Dict[str, float],
        context: Optional[Dict[str, Any]] = None,
    ) -> Explanation:
        """
        Generate explanation for mood-based recommendation.

        Args:
            track_id: ID of recommended track
            mood: Detected/specified mood
            mood_score: Mood matching score
            track_features: Audio features of the track
            context: Optional context (time, activity, weather)

        Returns:
            Explanation object
        """
        # Get mood template
        summary = self.MOOD_TEMPLATES.get(
            mood.lower(),
            f"This track matches your {mood} mood",
        )

        details = []

        # Add valence/energy explanation
        valence = track_features.get("valence", 0.5)
        energy = track_features.get("energy", 0.5)

        valence_level = self._get_feature_level(valence)
        energy_level = self._get_feature_level(energy)

        valence_info = self.FEATURE_INFO["valence"]
        energy_info = self.FEATURE_INFO["energy"]

        details.append(f"Track is {valence_info[valence_level]}")
        details.append(f"Track is {energy_info[energy_level]}")

        # Add context factors
        context_factors = []
        if context:
            for ctx_type, ctx_value in context.items():
                if ctx_type in self.CONTEXT_TEMPLATES and ctx_value:
                    templates = self.CONTEXT_TEMPLATES[ctx_type]
                    if ctx_value in templates:
                        context_factors.append(templates[ctx_value])

        # Calculate feature contributions for valence/energy
        contributions = []
        # For mood, we care most about valence and energy
        mood_targets = self._get_mood_targets(mood)
        for feature in ["valence", "energy"]:
            if feature in track_features:
                contrib = self._calculate_feature_contribution(
                    feature,
                    track_features[feature],
                    mood_targets.get(feature, 0.5),
                )
                contributions.append(contrib)

        return Explanation(
            track_id=track_id,
            primary_reason=ExplanationType.MOOD_MATCH,
            confidence=mood_score,
            summary=summary,
            details=details,
            feature_contributions=contributions,
            model_contributions={"sentiment": 1.0},
            context_factors=context_factors,
        )

    def _get_mood_targets(self, mood: str) -> Dict[str, float]:
        """Get target valence/energy for a mood."""
        mood_targets = {
            "happy": {"valence": 0.8, "energy": 0.7},
            "sad": {"valence": 0.2, "energy": 0.3},
            "energetic": {"valence": 0.65, "energy": 0.85},
            "calm": {"valence": 0.6, "energy": 0.3},
            "angry": {"valence": 0.3, "energy": 0.85},
            "relaxed": {"valence": 0.65, "energy": 0.25},
            "excited": {"valence": 0.75, "energy": 0.88},
            "melancholic": {"valence": 0.35, "energy": 0.4},
            "peaceful": {"valence": 0.6, "energy": 0.2},
            "anxious": {"valence": 0.4, "energy": 0.75},
        }
        return mood_targets.get(mood.lower(), {"valence": 0.5, "energy": 0.5})

    def explain_hybrid(
        self,
        track_id: str,
        model_scores: Dict[str, float],
        model_weights: Dict[str, float],
        track_features: Optional[Dict[str, float]] = None,
        seed_features: Optional[Dict[str, float]] = None,
        mood: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Explanation:
        """
        Generate explanation for hybrid recommendation.

        Combines explanations from multiple models based on their contributions.

        Args:
            track_id: ID of recommended track
            model_scores: Scores from each model component
            model_weights: Weights of each model
            track_features: Audio features of recommended track
            seed_features: Audio features of seed track (if content-based)
            mood: Detected mood (if sentiment-aware)
            context: Context factors

        Returns:
            Combined Explanation object
        """
        # Calculate weighted contributions
        contributions = {}
        total_contribution = 0

        for model, score in model_scores.items():
            weight = model_weights.get(model, 0)
            contribution = score * weight
            contributions[model] = contribution
            total_contribution += contribution

        # Normalize contributions
        if total_contribution > 0:
            contributions = {
                k: v / total_contribution for k, v in contributions.items()
            }

        # Find primary contributor
        primary_model = max(contributions.items(), key=lambda x: x[1])[0]

        # Generate summary based on primary contributor
        summaries = {
            "content": "Recommended for its similar sound",
            "collaborative": "Popular with listeners like you",
            "sentiment": f"Matches your {mood or 'current'} mood",
        }
        summary = summaries.get(primary_model, "Recommended for you")

        # Collect details from all contributing models
        details = []

        if contributions.get("content", 0) > 0.2 and track_features and seed_features:
            details.append("Similar audio characteristics to tracks you like")

        if contributions.get("collaborative", 0) > 0.2:
            details.append("Enjoyed by users with similar taste")

        if contributions.get("sentiment", 0) > 0.2 and mood:
            details.append(f"Matches your {mood} mood")

        # Add context factors
        context_factors = []
        if context:
            for ctx_type, ctx_value in context.items():
                if ctx_type in self.CONTEXT_TEMPLATES and ctx_value:
                    templates = self.CONTEXT_TEMPLATES[ctx_type]
                    if ctx_value in templates:
                        context_factors.append(templates[ctx_value])

        # Calculate feature contributions if we have features
        feature_contributions = []
        if track_features and seed_features:
            for feature in self.FEATURE_INFO.keys():
                if feature in track_features and feature in seed_features:
                    contrib = self._calculate_feature_contribution(
                        feature,
                        track_features.get(feature, 0.5),
                        seed_features.get(feature, 0.5),
                    )
                    feature_contributions.append(contrib)
            feature_contributions.sort(key=lambda x: x.contribution_score, reverse=True)

        # Determine primary reason
        reason_map = {
            "content": ExplanationType.SIMILAR_AUDIO,
            "collaborative": ExplanationType.SIMILAR_USERS,
            "sentiment": ExplanationType.MOOD_MATCH,
        }
        primary_reason = reason_map.get(primary_model, ExplanationType.SIMILAR_AUDIO)

        # Calculate overall confidence
        confidence = sum(
            model_scores.get(m, 0) * model_weights.get(m, 0)
            for m in model_scores.keys()
        )

        return Explanation(
            track_id=track_id,
            primary_reason=primary_reason,
            confidence=min(confidence, 1.0),
            summary=summary,
            details=details,
            feature_contributions=feature_contributions[:5],  # Top 5
            model_contributions=contributions,
            context_factors=context_factors,
        )

    def format_explanation(self, explanation: Explanation) -> Dict[str, Any]:
        """
        Format an explanation for API response.

        Args:
            explanation: Explanation object

        Returns:
            Dict suitable for JSON response
        """
        return {
            "track_id": explanation.track_id,
            "reason": explanation.primary_reason.value,
            "confidence": round(explanation.confidence, 3),
            "summary": explanation.summary,
            "details": explanation.details,
            "model_contributions": {
                k: round(v, 3) for k, v in explanation.model_contributions.items()
            },
            "context_factors": explanation.context_factors,
            "top_features": [
                {
                    "feature": fc.feature,
                    "description": fc.description,
                    "contribution": round(fc.contribution_score, 3),
                }
                for fc in explanation.feature_contributions[:3]
            ],
        }


# Singleton instance
_explainer: Optional[RecommendationExplainer] = None


def get_explainer() -> RecommendationExplainer:
    """Get the singleton explainer instance."""
    global _explainer
    if _explainer is None:
        _explainer = RecommendationExplainer()
    return _explainer
