"""
Evaluation metrics for recommendation systems
"""

import logging
from typing import Dict, List, Set

import numpy as np

logger = logging.getLogger(__name__)


def precision_at_k(recommended: List[str], relevant: Set[str], k: int) -> float:
    """
    Calculate Precision@K.

    Precision@K = (# of recommended items that are relevant in top-K) / K

    Args:
        recommended: List of recommended track IDs (in order)
        relevant: Set of relevant/ground truth track IDs
        k: Number of top recommendations to consider

    Returns:
        Precision@K score (0.0 to 1.0)
    """
    if k <= 0:
        return 0.0

    recommended_at_k = recommended[:k]
    hits = len(set(recommended_at_k) & relevant)
    return hits / k


def recall_at_k(recommended: List[str], relevant: Set[str], k: int) -> float:
    """
    Calculate Recall@K.

    Recall@K = (# of recommended items that are relevant in top-K) / (# of relevant items)

    Args:
        recommended: List of recommended track IDs (in order)
        relevant: Set of relevant/ground truth track IDs
        k: Number of top recommendations to consider

    Returns:
        Recall@K score (0.0 to 1.0)
    """
    if not relevant or k <= 0:
        return 0.0

    recommended_at_k = recommended[:k]
    hits = len(set(recommended_at_k) & relevant)
    return hits / len(relevant)


def ndcg_at_k(recommended: List[str], relevant: Set[str], k: int) -> float:
    """
    Calculate Normalized Discounted Cumulative Gain at K (NDCG@K).

    NDCG accounts for the position of relevant items in the ranking.
    Items appearing earlier get higher scores.

    Args:
        recommended: List of recommended track IDs (in order)
        relevant: Set of relevant/ground truth track IDs
        k: Number of top recommendations to consider

    Returns:
        NDCG@K score (0.0 to 1.0)
    """
    if k <= 0 or not relevant:
        return 0.0

    recommended_at_k = recommended[:k]

    # Calculate DCG
    dcg = 0.0
    for i, track_id in enumerate(recommended_at_k):
        if track_id in relevant:
            # Using binary relevance (1 if relevant, 0 otherwise)
            dcg += 1.0 / np.log2(
                i + 2
            )  # +2 because position is 1-indexed and log2(1)=0

    # Calculate ideal DCG (IDCG)
    # Best case: all relevant items at the top positions
    n_relevant = min(len(relevant), k)
    idcg = sum(1.0 / np.log2(i + 2) for i in range(n_relevant))

    if idcg == 0:
        return 0.0

    return dcg / idcg


def mean_reciprocal_rank(recommended: List[str], relevant: Set[str]) -> float:
    """
    Calculate Mean Reciprocal Rank (MRR).

    MRR = 1 / (position of first relevant item)

    Args:
        recommended: List of recommended track IDs (in order)
        relevant: Set of relevant/ground truth track IDs

    Returns:
        MRR score (0.0 to 1.0)
    """
    for i, track_id in enumerate(recommended):
        if track_id in relevant:
            return 1.0 / (i + 1)
    return 0.0


def hit_rate_at_k(recommended: List[str], relevant: Set[str], k: int) -> float:
    """
    Calculate Hit Rate at K.

    Hit Rate@K = 1 if any relevant item is in top-K, else 0

    Args:
        recommended: List of recommended track IDs
        relevant: Set of relevant track IDs
        k: Number of top recommendations

    Returns:
        1.0 if hit, 0.0 otherwise
    """
    if k <= 0 or not relevant:
        return 0.0

    recommended_at_k = set(recommended[:k])
    return 1.0 if recommended_at_k & relevant else 0.0


def coverage(all_recommendations: List[List[str]], catalog_size: int) -> float:
    """
    Calculate catalog coverage.

    Coverage = (# of unique items recommended) / (total catalog size)

    Args:
        all_recommendations: List of recommendation lists for all users
        catalog_size: Total number of items in catalog

    Returns:
        Coverage score (0.0 to 1.0)
    """
    if catalog_size <= 0:
        return 0.0

    unique_recommended = set()
    for recs in all_recommendations:
        unique_recommended.update(recs)

    return len(unique_recommended) / catalog_size


def diversity(
    recommendations: List[Dict], feature_key: str = "audio_features"
) -> float:
    """
    Calculate intra-list diversity based on audio features.

    Diversity = average pairwise distance between recommended items

    Args:
        recommendations: List of recommendation dicts with audio features
        feature_key: Key containing audio features dict

    Returns:
        Diversity score (0.0 to 1.0)
    """
    if len(recommendations) < 2:
        return 0.0

    # Extract feature vectors
    features = ["danceability", "energy", "valence", "acousticness", "instrumentalness"]
    vectors = []

    for rec in recommendations:
        audio = rec.get(feature_key, {})
        if audio:
            vector = [audio.get(f, 0.5) for f in features]
            vectors.append(vector)

    if len(vectors) < 2:
        return 0.0

    # Calculate average pairwise Euclidean distance
    vectors = np.array(vectors)
    total_distance = 0.0
    n_pairs = 0

    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            distance = np.linalg.norm(vectors[i] - vectors[j])
            total_distance += distance
            n_pairs += 1

    # Normalize by maximum possible distance (sqrt(5) for 5 features in [0,1])
    max_distance = np.sqrt(len(features))
    avg_distance = total_distance / n_pairs if n_pairs > 0 else 0.0

    return avg_distance / max_distance


def evaluate_recommendations(
    recommended: List[str], relevant: Set[str], k_values: List[int] = [5, 10, 20]
) -> Dict[str, float]:
    """
    Calculate all metrics for a single user's recommendations.

    Args:
        recommended: List of recommended track IDs (in order)
        relevant: Set of relevant track IDs
        k_values: List of K values to evaluate

    Returns:
        Dict of metric names to scores
    """
    results = {}

    for k in k_values:
        results[f"precision@{k}"] = precision_at_k(recommended, relevant, k)
        results[f"recall@{k}"] = recall_at_k(recommended, relevant, k)
        results[f"ndcg@{k}"] = ndcg_at_k(recommended, relevant, k)
        results[f"hit_rate@{k}"] = hit_rate_at_k(recommended, relevant, k)

    results["mrr"] = mean_reciprocal_rank(recommended, relevant)

    return results


def aggregate_metrics(all_user_metrics: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Aggregate metrics across all users.

    Args:
        all_user_metrics: List of metric dicts for each user

    Returns:
        Dict of averaged metrics
    """
    if not all_user_metrics:
        return {}

    # Collect all metric names
    metric_names = set()
    for user_metrics in all_user_metrics:
        metric_names.update(user_metrics.keys())

    # Calculate averages
    aggregated = {}
    for metric in metric_names:
        values = [m.get(metric, 0.0) for m in all_user_metrics if metric in m]
        if values:
            aggregated[metric] = np.mean(values)
            aggregated[f"{metric}_std"] = np.std(values)

    aggregated["n_users"] = len(all_user_metrics)

    return aggregated
