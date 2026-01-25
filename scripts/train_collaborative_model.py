#!/usr/bin/env python
"""
Training script for the collaborative filtering recommendation model.

This script:
1. Loads synthetic user interaction data
2. Builds the user-item interaction matrix
3. Trains ALS matrix factorization model
4. Validates recommendations
5. Saves the trained model

Usage:
    python scripts/train_collaborative_model.py [--n-factors N] [--iterations N]
"""

import argparse
import json
import logging
import os
import sys
import time

import numpy as np
from scipy import sparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml.collaborative import CollaborativeFilteringRecommender
from app.ml.model_persistence import load_model_metadata, save_model

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_SYNTHETIC_DIR = "data/synthetic"
DEFAULT_MODELS_DIR = "data/models"


def load_synthetic_data(synthetic_dir: str) -> tuple:
    """
    Load synthetic interaction data.

    Returns:
        tuple: (interaction_matrix, user_ids, track_ids, stats)
    """
    logger.info(f"Loading synthetic data from {synthetic_dir}...")

    # Load interaction matrix
    matrix_path = os.path.join(synthetic_dir, "interaction_matrix.npz")
    if not os.path.exists(matrix_path):
        raise FileNotFoundError(f"Interaction matrix not found at {matrix_path}")

    interaction_matrix = sparse.load_npz(matrix_path)
    logger.info(f"Loaded interaction matrix: {interaction_matrix.shape}")

    # Load user IDs
    users_path = os.path.join(synthetic_dir, "synthetic_users.json")
    with open(users_path, "r") as f:
        users = json.load(f)
    user_ids = [u["user_id"] for u in users]

    # Load track IDs
    track_mapping_path = os.path.join(synthetic_dir, "track_id_mapping.json")
    with open(track_mapping_path, "r") as f:
        track_ids = json.load(f)

    # Load stats
    stats_path = os.path.join(synthetic_dir, "generation_stats.json")
    with open(stats_path, "r") as f:
        stats = json.load(f)

    logger.info(f"  Users: {len(user_ids):,}")
    logger.info(f"  Tracks: {len(track_ids):,}")
    logger.info(f"  Interactions: {interaction_matrix.nnz:,}")

    return interaction_matrix, user_ids, track_ids, stats


def validate_model(
    model: CollaborativeFilteringRecommender,
    user_ids: list,
    n_test_users: int = 10,
) -> dict:
    """Run validation tests on the trained model."""
    logger.info("Validating model...")

    results = {
        "is_fitted": model.is_fitted,
        "n_users": len(model.user_mapping) if model.user_mapping else 0,
        "n_tracks": len(model.track_mapping) if model.track_mapping else 0,
        "tests_passed": 0,
        "tests_failed": 0,
    }

    # Test 1: Recommendations for random users
    try:
        test_users = np.random.choice(
            user_ids, size=min(n_test_users, len(user_ids)), replace=False
        )
        all_recs = []

        for user_id in test_users:
            recs = model.recommend_for_user(user_id, n_recommendations=10)
            assert len(recs) > 0, f"No recommendations for user {user_id}"
            assert all("track_id" in r for r in recs), "Missing track_id"
            assert all("cf_score" in r for r in recs), "Missing cf_score"
            all_recs.extend(recs)

        results["tests_passed"] += 1
        logger.info(f"  PASS: recommend_for_user() for {n_test_users} users")
    except Exception as e:
        results["tests_failed"] += 1
        logger.error(f"  FAIL: recommend_for_user() - {e}")

    # Test 2: Similar users
    try:
        test_user = user_ids[0]
        similar = model.get_similar_users(test_user, n_users=5)
        assert len(similar) > 0, "No similar users found"
        assert all("user_id" in s for s in similar), "Missing user_id"
        assert all("similarity" in s for s in similar), "Missing similarity"

        results["tests_passed"] += 1
        logger.info("  PASS: get_similar_users()")
    except Exception as e:
        results["tests_failed"] += 1
        logger.error(f"  FAIL: get_similar_users() - {e}")

    # Test 3: CF scores in valid range
    try:
        test_user = user_ids[0]
        recs = model.recommend_for_user(test_user, n_recommendations=20)
        scores = [r["cf_score"] for r in recs]

        # Scores should be positive and sorted descending
        assert all(s >= 0 for s in scores), "Negative CF scores"
        assert scores == sorted(scores, reverse=True), "Scores not sorted"

        results["tests_passed"] += 1
        logger.info("  PASS: CF scores valid and sorted")
    except Exception as e:
        results["tests_failed"] += 1
        logger.error(f"  FAIL: CF score validation - {e}")

    # Test 4: Latency test
    try:
        times = []
        test_users = np.random.choice(user_ids, size=20, replace=False)

        for user_id in test_users:
            start = time.time()
            model.recommend_for_user(user_id, n_recommendations=10)
            times.append(time.time() - start)

        avg_time = np.mean(times) * 1000
        results["avg_latency_ms"] = round(avg_time, 2)

        if avg_time < 50:
            results["tests_passed"] += 1
            logger.info(f"  PASS: avg latency {avg_time:.2f}ms < 50ms target")
        else:
            results["tests_failed"] += 1
            logger.warning(f"  WARN: avg latency {avg_time:.2f}ms > 50ms target")
    except Exception as e:
        results["tests_failed"] += 1
        logger.error(f"  FAIL: latency test - {e}")

    # Test 5: Coverage - unique tracks recommended
    try:
        all_recommended = set()
        sample_users = np.random.choice(
            user_ids, size=min(100, len(user_ids)), replace=False
        )

        for user_id in sample_users:
            recs = model.recommend_for_user(user_id, n_recommendations=20)
            for r in recs:
                all_recommended.add(r["track_id"])

        coverage = len(all_recommended) / len(model.track_mapping)
        results["coverage"] = round(coverage, 4)

        if coverage > 0.05:  # At least 5% catalog coverage
            results["tests_passed"] += 1
            logger.info(f"  PASS: coverage {coverage:.2%} > 5% target")
        else:
            results["tests_failed"] += 1
            logger.warning(f"  WARN: coverage {coverage:.2%} < 5% target")
    except Exception as e:
        results["tests_failed"] += 1
        logger.error(f"  FAIL: coverage test - {e}")

    return results


def train_model(
    synthetic_dir: str = DEFAULT_SYNTHETIC_DIR,
    models_dir: str = DEFAULT_MODELS_DIR,
    n_factors: int = 50,
    regularization: float = 0.1,
    iterations: int = 50,
    save_version: str = None,
) -> dict:
    """
    Train and save the collaborative filtering model.

    Args:
        synthetic_dir: Directory with synthetic data
        models_dir: Directory to save models
        n_factors: Number of latent factors
        regularization: ALS regularization parameter
        iterations: Number of ALS iterations
        save_version: Version string

    Returns:
        dict: Training results
    """
    start_time = time.time()

    # Load data
    interaction_matrix, user_ids, track_ids, data_stats = load_synthetic_data(
        synthetic_dir
    )

    # Initialize model
    logger.info(f"Training CollaborativeFilteringRecommender...")
    logger.info(f"  n_factors: {n_factors}")
    logger.info(f"  regularization: {regularization}")
    logger.info(f"  iterations: {iterations}")

    model = CollaborativeFilteringRecommender(
        n_factors=n_factors,
        regularization=regularization,
        iterations=iterations,
    )

    # Train
    train_start = time.time()
    model.fit(interaction_matrix, user_ids, track_ids)
    train_time = time.time() - train_start

    if not model.is_fitted:
        logger.error("Model training failed!")
        return {"success": False, "error": "Model did not fit"}

    logger.info(f"Model fitted in {train_time:.2f}s")

    # Validate
    validation_results = validate_model(model, user_ids)

    # Prepare metadata
    metadata = {
        "model_type": "collaborative_filtering",
        "algorithm": "ALS",
        "n_factors": n_factors,
        "regularization": regularization,
        "iterations": iterations,
        "n_users": len(user_ids),
        "n_tracks": len(track_ids),
        "n_interactions": interaction_matrix.nnz,
        "matrix_density": float(
            interaction_matrix.nnz / (len(user_ids) * len(track_ids))
        ),
        "train_time_seconds": round(train_time, 2),
        "validation": validation_results,
        "synthetic_data_dir": synthetic_dir,
    }

    # Save model
    os.makedirs(models_dir, exist_ok=True)
    model_path = save_model(
        model=model,
        model_name="collaborative",
        version=save_version,
        metadata=metadata,
        models_dir=models_dir,
    )

    total_time = time.time() - start_time

    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("TRAINING SUMMARY")
    logger.info("=" * 50)
    logger.info(f"  Users:            {len(user_ids):,}")
    logger.info(f"  Tracks:           {len(track_ids):,}")
    logger.info(f"  Interactions:     {interaction_matrix.nnz:,}")
    logger.info(f"  Latent factors:   {n_factors}")
    logger.info(f"  Train time:       {train_time:.2f}s")
    logger.info(
        f"  Validation:       {validation_results['tests_passed']}/{validation_results['tests_passed'] + validation_results['tests_failed']} tests passed"
    )
    if "avg_latency_ms" in validation_results:
        logger.info(f"  Avg latency:      {validation_results['avg_latency_ms']:.2f}ms")
    if "coverage" in validation_results:
        logger.info(f"  Coverage:         {validation_results['coverage']:.2%}")
    logger.info(f"  Model saved to:   {model_path}")
    logger.info("=" * 50)

    return {
        "model_path": model_path,
        "metadata": metadata,
        "success": validation_results["tests_failed"] == 0,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Train the collaborative filtering model"
    )
    parser.add_argument(
        "--synthetic-dir",
        type=str,
        default=DEFAULT_SYNTHETIC_DIR,
        help="Directory with synthetic data",
    )
    parser.add_argument(
        "--models-dir",
        type=str,
        default=DEFAULT_MODELS_DIR,
        help="Directory to save models",
    )
    parser.add_argument(
        "--n-factors",
        type=int,
        default=50,
        help="Number of latent factors (default: 50)",
    )
    parser.add_argument(
        "--regularization",
        type=float,
        default=0.1,
        help="Regularization parameter (default: 0.1)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=50,
        help="Number of ALS iterations (default: 50)",
    )
    parser.add_argument(
        "--version",
        type=str,
        default=None,
        help="Model version string",
    )

    args = parser.parse_args()

    try:
        results = train_model(
            synthetic_dir=args.synthetic_dir,
            models_dir=args.models_dir,
            n_factors=args.n_factors,
            regularization=args.regularization,
            iterations=args.iterations,
            save_version=args.version,
        )

        if results["success"]:
            logger.info("Training completed successfully!")
            sys.exit(0)
        else:
            logger.warning("Training completed with validation warnings")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Training failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
