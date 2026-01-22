#!/usr/bin/env python
"""
Evaluation script for NextTrack recommendation models

Compares models against baselines using standard metrics:
- Precision@K
- Recall@K
- NDCG@K
- Coverage
- Diversity

Usage:
    python scripts/evaluate.py
    python scripts/evaluate.py --k 10 --n-users 1000
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List

import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml.baselines import ContentBasedBaseline, PopularityBaseline, RandomBaseline
from app.ml.data_split import create_track_splits, get_user_ground_truth
from app.ml.metrics import (
    aggregate_metrics,
    coverage,
    diversity,
    evaluate_recommendations,
)
from app.services.dataset_service import DatasetService

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def generate_synthetic_interactions(
    tracks_df: pd.DataFrame,
    n_users: int = 100,
    interactions_per_user: tuple = (10, 50),
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Generate synthetic user interactions for evaluation.

    Creates realistic-ish interactions where users prefer tracks
    with similar audio features.

    Args:
        tracks_df: DataFrame with track features
        n_users: Number of synthetic users
        interactions_per_user: (min, max) interactions per user
        random_state: Random seed

    Returns:
        DataFrame with synthetic interactions
    """
    np.random.seed(random_state)

    id_col = "id" if "id" in tracks_df.columns else "track_id"
    track_ids = tracks_df[id_col].values
    n_tracks = len(track_ids)

    interactions = []

    for user_idx in range(n_users):
        user_id = f"user_{user_idx}"
        n_interactions = np.random.randint(
            interactions_per_user[0], interactions_per_user[1] + 1
        )

        # Give each user a preference profile (random point in feature space)
        user_pref = {
            "valence": np.random.uniform(0.2, 0.8),
            "energy": np.random.uniform(0.2, 0.8),
            "danceability": np.random.uniform(0.2, 0.8),
        }

        # Calculate affinity to each track based on feature similarity
        affinity = np.zeros(n_tracks)
        for feature, pref_value in user_pref.items():
            if feature in tracks_df.columns:
                affinity -= (tracks_df[feature].fillna(0.5).values - pref_value) ** 2

        # Convert to probabilities
        affinity = np.exp(affinity * 5)  # Scale factor
        probs = affinity / affinity.sum()

        # Sample tracks based on affinity
        sampled_indices = np.random.choice(
            n_tracks, size=n_interactions, replace=False, p=probs
        )

        for idx in sampled_indices:
            interactions.append(
                {
                    "user_id": user_id,
                    "track_id": track_ids[idx],
                    "rating": np.random.uniform(3.5, 5.0),  # Positive interactions
                    "play_count": np.random.randint(1, 10),
                }
            )

    logger.info(
        f"Generated {len(interactions)} synthetic interactions for {n_users} users"
    )
    return pd.DataFrame(interactions)


def evaluate_model(
    model,
    model_name: str,
    test_ground_truth: Dict[str, List[str]],
    k_values: List[int],
    tracks_df: pd.DataFrame,
    exclude_per_user: Dict[str, List[str]] = None,
) -> Dict:
    """
    Evaluate a single model.

    Args:
        model: Model with recommend() method
        model_name: Name for reporting
        test_ground_truth: Dict of user_id -> relevant track_ids
        k_values: List of K values to evaluate
        tracks_df: For coverage calculation
        exclude_per_user: Tracks to exclude per user (training data)

    Returns:
        Dict with evaluation results
    """
    logger.info(f"Evaluating {model_name}...")

    all_user_metrics = []
    all_recommendations = []

    max_k = max(k_values)

    for user_id, relevant_tracks in test_ground_truth.items():
        # Get recommendations
        exclude = exclude_per_user.get(user_id, []) if exclude_per_user else []

        try:
            recs = model.recommend(
                user_id=user_id, n_recommendations=max_k, exclude_tracks=exclude
            )
            recommended_ids = [r["track_id"] for r in recs]
        except Exception as e:
            logger.warning(f"Error getting recommendations for {user_id}: {e}")
            recommended_ids = []

        # Calculate metrics
        relevant_set = set(relevant_tracks)
        user_metrics = evaluate_recommendations(recommended_ids, relevant_set, k_values)
        all_user_metrics.append(user_metrics)
        all_recommendations.append(recommended_ids)

    # Aggregate metrics
    results = aggregate_metrics(all_user_metrics)

    # Calculate coverage
    id_col = "id" if "id" in tracks_df.columns else "track_id"
    catalog_size = len(tracks_df[id_col].unique())
    results["coverage"] = coverage(all_recommendations, catalog_size)

    results["model"] = model_name
    results["timestamp"] = datetime.now().isoformat()

    return results


def run_evaluation(
    n_users: int = 100, k_values: List[int] = [5, 10, 20], output_file: str = None
):
    """
    Run full evaluation comparing models against baselines.

    Args:
        n_users: Number of synthetic users for evaluation
        k_values: K values for metrics
        output_file: Optional path to save results JSON
    """
    logger.info("=" * 60)
    logger.info("NextTrack Model Evaluation")
    logger.info("=" * 60)

    # Load dataset
    dataset = DatasetService()
    if not dataset.load_dataset():
        logger.error("Failed to load dataset")
        return

    tracks_df = dataset.tracks_df
    logger.info(f"Loaded {len(tracks_df)} tracks")

    # Generate synthetic interactions
    interactions_df = generate_synthetic_interactions(
        tracks_df, n_users=n_users, interactions_per_user=(20, 50)
    )

    # Split interactions into train/test
    from app.ml.data_split import create_interaction_splits

    train_df, val_df, test_df = create_interaction_splits(
        interactions_df, test_size=0.2, val_size=0.1, min_interactions_per_user=5
    )

    # Get ground truth from test set
    test_ground_truth = get_user_ground_truth(test_df)

    # Get training tracks per user (to exclude from recommendations)
    train_tracks_per_user = (
        train_df.groupby("user_id")["track_id"].apply(list).to_dict()
    )

    logger.info(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
    logger.info(f"Users in test set: {len(test_ground_truth)}")

    # Initialize models
    models = {}

    # Popularity baseline
    pop_model = PopularityBaseline()
    pop_model.fit(tracks_df=tracks_df)
    models["Popularity Baseline"] = pop_model

    # Random baseline
    random_model = RandomBaseline()
    random_model.fit(tracks_df=tracks_df)
    models["Random Baseline"] = random_model

    # Content-based baseline
    content_model = ContentBasedBaseline()
    content_model.fit(tracks_df=tracks_df)
    models["Content-Based Baseline"] = content_model

    # Evaluate all models
    all_results = []

    for model_name, model in models.items():
        results = evaluate_model(
            model=model,
            model_name=model_name,
            test_ground_truth=test_ground_truth,
            k_values=k_values,
            tracks_df=tracks_df,
            exclude_per_user=train_tracks_per_user,
        )
        all_results.append(results)

    # Print results
    logger.info("\n" + "=" * 60)
    logger.info("EVALUATION RESULTS")
    logger.info("=" * 60)

    # Create comparison table
    metrics_to_show = (
        [f"precision@{k}" for k in k_values]
        + [f"recall@{k}" for k in k_values]
        + [f"ndcg@{k}" for k in k_values]
        + ["mrr", "coverage"]
    )

    print("\n{:<25} ".format("Model"), end="")
    for metric in metrics_to_show:
        print(f"{metric:>12}", end="")
    print()
    print("-" * (25 + len(metrics_to_show) * 13))

    for result in all_results:
        print(f"{result['model']:<25} ", end="")
        for metric in metrics_to_show:
            value = result.get(metric, 0.0)
            print(f"{value:>12.4f}", end="")
        print()

    # Save results
    if output_file:
        with open(output_file, "w") as f:
            json.dump(all_results, f, indent=2)
        logger.info(f"\nResults saved to {output_file}")

    # Print targets comparison
    print("\n" + "=" * 60)
    print("TARGET COMPARISON (from project.md)")
    print("=" * 60)
    targets = {"precision@10": 0.3, "recall@10": 0.2, "ndcg@10": 0.4, "coverage": 0.3}

    for result in all_results:
        print(f"\n{result['model']}:")
        for metric, target in targets.items():
            actual = result.get(metric, 0.0)
            status = "PASS" if actual >= target else "FAIL"
            print(f"  {metric}: {actual:.4f} (target: {target}) [{status}]")

    return all_results


def main():
    parser = argparse.ArgumentParser(description="Evaluate recommendation models")
    parser.add_argument(
        "--n-users",
        type=int,
        default=100,
        help="Number of synthetic users for evaluation",
    )
    parser.add_argument(
        "--k",
        type=int,
        nargs="+",
        default=[5, 10, 20],
        help="K values for metrics (e.g., --k 5 10 20)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/evaluation_results.json",
        help="Output file for results",
    )

    args = parser.parse_args()

    run_evaluation(n_users=args.n_users, k_values=args.k, output_file=args.output)


if __name__ == "__main__":
    main()
