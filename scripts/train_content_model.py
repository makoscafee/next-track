#!/usr/bin/env python
"""
Training script for the content-based recommendation model.

This script:
1. Loads the full tracks dataset
2. Preprocesses and validates audio features
3. Trains the K-NN content-based model
4. Saves the trained model with versioning
5. Runs basic validation tests

Usage:
    python scripts/train_content_model.py [--n-neighbors N] [--batch-size N]
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml.content_based import ContentBasedRecommender
from app.ml.data_quality import CONTENT_MODEL_FEATURES, DataPreprocessor
from app.ml.model_persistence import load_model_metadata, save_model

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Audio features used by the model
AUDIO_FEATURES = CONTENT_MODEL_FEATURES

# Default paths
DEFAULT_DATASET_PATH = "data/processed/tracks.csv"
DEFAULT_MODELS_DIR = "data/models"


def load_dataset(dataset_path: str) -> pd.DataFrame:
    """Load and validate the tracks dataset."""
    logger.info(f"Loading dataset from {dataset_path}...")

    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")

    df = pd.read_csv(dataset_path)
    logger.info(f"Loaded {len(df):,} tracks")

    return df


def preprocess_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess audio features for training using the data quality pipeline.

    - Validates data quality
    - Handles missing values (median imputation)
    - Detects and clips outliers
    - Normalizes tempo to 0-1 scale
    - Filters out tracks with too many missing features
    - Removes duplicates
    """
    logger.info("Preprocessing features...")

    # Select relevant columns before preprocessing
    required_cols = ["id"] + AUDIO_FEATURES
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    extra_cols = [c for c in ["name", "artists"] if c in df.columns]
    df = df[required_cols + extra_cols].copy()

    preprocessor = DataPreprocessor(
        features=AUDIO_FEATURES,
        max_missing_features=2,
        handle_outliers=True,
        iqr_multiplier=1.5,
    )
    df, quality_report = preprocessor.preprocess(df, validate=True)

    logger.info(
        f"Quality report: {quality_report['input_rows']:,} -> "
        f"{quality_report['output_rows']:,} tracks"
    )

    # Rename id to track_id for the model
    df = df.rename(columns={"id": "track_id"})

    return df


def validate_model(model: ContentBasedRecommender, df: pd.DataFrame) -> dict:
    """Run basic validation tests on the trained model."""
    logger.info("Validating model...")

    results = {
        "is_fitted": model.is_fitted,
        "n_tracks": len(model.track_ids),
        "tests_passed": 0,
        "tests_failed": 0,
    }

    # Test 1: Recommend from features
    try:
        seed_features = {f: 0.5 for f in AUDIO_FEATURES}
        recs = model.recommend(seed_features, n_recommendations=10)
        assert len(recs) == 10, f"Expected 10 recommendations, got {len(recs)}"
        assert all("track_id" in r for r in recs), "Missing track_id in recommendations"
        assert all("similarity_score" in r for r in recs), "Missing similarity_score"
        results["tests_passed"] += 1
        logger.info("  PASS: recommend() from features")
    except Exception as e:
        results["tests_failed"] += 1
        logger.error(f"  FAIL: recommend() from features - {e}")

    # Test 2: Recommend from track ID
    try:
        sample_id = df["track_id"].iloc[0]
        recs = model.recommend_from_track_id(sample_id, n_recommendations=10)
        assert len(recs) == 10, f"Expected 10 recommendations, got {len(recs)}"
        assert sample_id not in [r["track_id"] for r in recs], (
            "Seed track in recommendations"
        )
        results["tests_passed"] += 1
        logger.info("  PASS: recommend_from_track_id()")
    except Exception as e:
        results["tests_failed"] += 1
        logger.error(f"  FAIL: recommend_from_track_id() - {e}")

    # Test 3: Check similarity scores are in valid range
    try:
        seed_features = {f: 0.7 for f in AUDIO_FEATURES}
        recs = model.recommend(seed_features, n_recommendations=10)
        scores = [r["similarity_score"] for r in recs]
        assert all(0 <= s <= 1 for s in scores), "Similarity scores out of range"
        assert scores == sorted(scores, reverse=True), "Scores not sorted descending"
        results["tests_passed"] += 1
        logger.info("  PASS: similarity scores valid and sorted")
    except Exception as e:
        results["tests_failed"] += 1
        logger.error(f"  FAIL: similarity score validation - {e}")

    # Test 4: Performance test (latency)
    try:
        seed_features = {f: np.random.random() for f in AUDIO_FEATURES}
        times = []
        for _ in range(10):
            start = time.time()
            model.recommend(seed_features, n_recommendations=20)
            times.append(time.time() - start)

        avg_time = np.mean(times) * 1000  # Convert to ms
        results["avg_latency_ms"] = round(avg_time, 2)

        if avg_time < 100:
            results["tests_passed"] += 1
            logger.info(f"  PASS: avg latency {avg_time:.2f}ms < 100ms target")
        else:
            results["tests_failed"] += 1
            logger.warning(f"  WARN: avg latency {avg_time:.2f}ms > 100ms target")
    except Exception as e:
        results["tests_failed"] += 1
        logger.error(f"  FAIL: performance test - {e}")

    return results


def train_model(
    dataset_path: str = DEFAULT_DATASET_PATH,
    models_dir: str = DEFAULT_MODELS_DIR,
    n_neighbors: int = 50,
    save_version: str = None,
) -> dict:
    """
    Train and save the content-based recommendation model.

    Args:
        dataset_path: Path to tracks CSV
        models_dir: Directory to save models
        n_neighbors: Number of neighbors for K-NN
        save_version: Version string (default: timestamp)

    Returns:
        dict: Training results and metadata
    """
    start_time = time.time()

    # Load and preprocess data
    df = load_dataset(dataset_path)
    df = preprocess_features(df)

    # Initialize and train model
    logger.info(f"Training ContentBasedRecommender with n_neighbors={n_neighbors}...")
    model = ContentBasedRecommender(n_neighbors=n_neighbors)

    train_start = time.time()
    model.fit(df)
    train_time = time.time() - train_start

    logger.info(f"Model fitted in {train_time:.2f}s on {len(df):,} tracks")

    # Validate model
    validation_results = validate_model(model, df)

    # Prepare metadata
    metadata = {
        "model_type": "content_based",
        "n_neighbors": n_neighbors,
        "n_tracks": len(df),
        "features": AUDIO_FEATURES,
        "train_time_seconds": round(train_time, 2),
        "validation": validation_results,
        "dataset_path": dataset_path,
    }

    # Save model
    os.makedirs(models_dir, exist_ok=True)
    model_path = save_model(
        model=model,
        model_name="content_based",
        version=save_version,
        metadata=metadata,
        models_dir=models_dir,
    )

    total_time = time.time() - start_time
    logger.info(f"Total training time: {total_time:.2f}s")
    logger.info(f"Model saved to: {model_path}")

    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("TRAINING SUMMARY")
    logger.info("=" * 50)
    logger.info(f"  Tracks:           {len(df):,}")
    logger.info(f"  Features:         {len(AUDIO_FEATURES)}")
    logger.info(f"  N-neighbors:      {n_neighbors}")
    logger.info(f"  Train time:       {train_time:.2f}s")
    logger.info(
        f"  Validation:       {validation_results['tests_passed']}/{validation_results['tests_passed'] + validation_results['tests_failed']} tests passed"
    )
    if "avg_latency_ms" in validation_results:
        logger.info(f"  Avg latency:      {validation_results['avg_latency_ms']:.2f}ms")
    logger.info("=" * 50)

    return {
        "model_path": model_path,
        "metadata": metadata,
        "success": validation_results["tests_failed"] == 0,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Train the content-based recommendation model"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=DEFAULT_DATASET_PATH,
        help="Path to tracks CSV dataset",
    )
    parser.add_argument(
        "--models-dir",
        type=str,
        default=DEFAULT_MODELS_DIR,
        help="Directory to save trained models",
    )
    parser.add_argument(
        "--n-neighbors",
        type=int,
        default=50,
        help="Number of neighbors for K-NN (default: 50)",
    )
    parser.add_argument(
        "--version",
        type=str,
        default=None,
        help="Model version string (default: timestamp)",
    )

    args = parser.parse_args()

    try:
        results = train_model(
            dataset_path=args.dataset,
            models_dir=args.models_dir,
            n_neighbors=args.n_neighbors,
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
        sys.exit(1)


if __name__ == "__main__":
    main()
