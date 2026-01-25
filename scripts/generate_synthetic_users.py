#!/usr/bin/env python
"""
Generate synthetic user interaction data for collaborative filtering.

This script creates realistic user-track interaction patterns based on:
1. User preference profiles (genre/mood preferences)
2. Track audio features (matching users to tracks they'd likely enjoy)
3. Popularity bias (popular tracks get more interactions)
4. Time-based patterns (recent tracks weighted higher)

Usage:
    python scripts/generate_synthetic_users.py --n-users 1000 --interactions-per-user 50
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from scipy import sparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# User preference archetypes
USER_ARCHETYPES = {
    "party_lover": {
        "danceability": (0.7, 0.15),
        "energy": (0.8, 0.1),
        "valence": (0.7, 0.15),
        "tempo": (0.5, 0.2),
        "acousticness": (0.2, 0.15),
        "weight": 0.20,
    },
    "chill_listener": {
        "danceability": (0.4, 0.15),
        "energy": (0.3, 0.15),
        "valence": (0.5, 0.2),
        "tempo": (0.3, 0.15),
        "acousticness": (0.7, 0.15),
        "weight": 0.20,
    },
    "workout_enthusiast": {
        "danceability": (0.6, 0.15),
        "energy": (0.85, 0.1),
        "valence": (0.6, 0.2),
        "tempo": (0.7, 0.15),
        "acousticness": (0.1, 0.1),
        "weight": 0.15,
    },
    "melancholic": {
        "danceability": (0.35, 0.15),
        "energy": (0.35, 0.15),
        "valence": (0.25, 0.15),
        "tempo": (0.35, 0.15),
        "acousticness": (0.6, 0.2),
        "weight": 0.15,
    },
    "eclectic": {
        "danceability": (0.5, 0.25),
        "energy": (0.5, 0.25),
        "valence": (0.5, 0.25),
        "tempo": (0.5, 0.25),
        "acousticness": (0.5, 0.25),
        "weight": 0.20,
    },
    "focus_worker": {
        "danceability": (0.3, 0.15),
        "energy": (0.4, 0.15),
        "valence": (0.45, 0.2),
        "tempo": (0.4, 0.15),
        "acousticness": (0.5, 0.2),
        "instrumentalness": (0.6, 0.2),
        "weight": 0.10,
    },
}

AUDIO_FEATURES = [
    "danceability",
    "energy",
    "valence",
    "tempo",
    "acousticness",
    "instrumentalness",
    "speechiness",
]


def load_tracks(dataset_path: str) -> pd.DataFrame:
    """Load tracks dataset."""
    logger.info(f"Loading tracks from {dataset_path}...")
    df = pd.read_csv(dataset_path)

    # Normalize tempo to 0-1
    if df["tempo"].max() > 1:
        df["tempo"] = df["tempo"].clip(0, 250) / 250.0

    # Fill missing values
    for feature in AUDIO_FEATURES:
        if feature in df.columns:
            df[feature] = df[feature].fillna(df[feature].median())

    logger.info(f"Loaded {len(df):,} tracks")
    return df


def generate_user_profile(archetype: str, user_id: int) -> dict:
    """Generate a user profile based on archetype with some randomness."""
    arch = USER_ARCHETYPES[archetype]

    profile = {
        "user_id": f"user_{user_id}",
        "archetype": archetype,
        "preferences": {},
    }

    for feature in AUDIO_FEATURES:
        if feature in arch:
            mean, std = arch[feature]
            # Add some individual variation
            profile["preferences"][feature] = np.clip(np.random.normal(mean, std), 0, 1)
        else:
            # Default preference with high variance
            profile["preferences"][feature] = np.random.uniform(0.2, 0.8)

    # How "picky" is this user (higher = stricter matching)
    profile["pickiness"] = np.random.uniform(0.3, 0.8)

    # How many tracks they typically interact with
    profile["activity_level"] = np.random.uniform(0.5, 1.5)

    return profile


def calculate_user_track_affinity(
    user_profile: dict, track_features: np.ndarray, feature_names: list
) -> float:
    """
    Calculate how much a user would like a track based on feature matching.

    Returns a score between 0 and 1.
    """
    prefs = user_profile["preferences"]
    pickiness = user_profile["pickiness"]

    # Calculate weighted distance
    total_diff = 0
    for i, feature in enumerate(feature_names):
        if feature in prefs:
            diff = abs(prefs[feature] - track_features[i])
            total_diff += diff

    avg_diff = total_diff / len(feature_names)

    # Convert distance to affinity score
    # Pickier users have steeper falloff
    affinity = np.exp(-pickiness * avg_diff * 5)

    return affinity


def generate_interactions(
    user_profile: dict,
    tracks_df: pd.DataFrame,
    n_interactions: int,
    popularity_scores: np.ndarray,
) -> list:
    """
    Generate synthetic interactions for a user.

    Uses a combination of:
    1. User-track affinity (based on feature matching)
    2. Popularity bias (popular tracks more likely to be discovered)
    3. Some randomness (serendipity)
    """
    feature_cols = [f for f in AUDIO_FEATURES if f in tracks_df.columns]
    track_features = tracks_df[feature_cols].values
    track_ids = tracks_df["id"].values

    # Calculate affinity scores for all tracks
    affinities = np.array(
        [
            calculate_user_track_affinity(user_profile, features, feature_cols)
            for features in track_features
        ]
    )

    # Combine with popularity (70% affinity, 30% popularity)
    combined_scores = 0.7 * affinities + 0.3 * popularity_scores

    # Add some noise for serendipity
    noise = np.random.uniform(0, 0.1, len(combined_scores))
    combined_scores = combined_scores + noise

    # Normalize to probabilities
    probs = combined_scores / combined_scores.sum()

    # Sample tracks based on probabilities
    n_to_sample = int(n_interactions * user_profile["activity_level"])
    n_to_sample = min(n_to_sample, len(track_ids))

    selected_indices = np.random.choice(
        len(track_ids),
        size=n_to_sample,
        replace=False,
        p=probs,
    )

    interactions = []
    base_time = datetime.now() - timedelta(days=90)

    for idx in selected_indices:
        track_id = track_ids[idx]
        affinity = affinities[idx]

        # Higher affinity = more plays, higher rating
        play_count = max(1, int(np.random.exponential(affinity * 5)))

        # Rating based on affinity with some noise
        if np.random.random() < 0.3:  # 30% chance of explicit rating
            rating = min(5, max(1, int(affinity * 5 + np.random.normal(0, 0.5))))
        else:
            rating = None

        # Interaction type based on affinity
        if affinity > 0.7:
            interaction_type = np.random.choice(
                ["play", "like", "save"], p=[0.5, 0.3, 0.2]
            )
        elif affinity > 0.4:
            interaction_type = np.random.choice(["play", "like"], p=[0.8, 0.2])
        else:
            interaction_type = "play"

        # Random timestamp within last 90 days
        days_ago = np.random.exponential(30)  # More recent interactions more likely
        timestamp = base_time + timedelta(days=min(days_ago, 90))

        interactions.append(
            {
                "user_id": user_profile["user_id"],
                "track_id": track_id,
                "interaction_type": interaction_type,
                "play_count": play_count,
                "rating": rating,
                "affinity_score": float(affinity),
                "timestamp": timestamp.isoformat(),
            }
        )

    return interactions


def build_interaction_matrix(
    interactions_df: pd.DataFrame,
    user_ids: list,
    track_ids: list,
) -> sparse.csr_matrix:
    """
    Build sparse user-item interaction matrix.

    Values are implicit feedback scores based on:
    - play_count (weighted)
    - interaction_type (like/save = higher weight)
    - rating if available
    """
    user_to_idx = {uid: idx for idx, uid in enumerate(user_ids)}
    track_to_idx = {tid: idx for idx, tid in enumerate(track_ids)}

    rows = []
    cols = []
    data = []

    for _, row in interactions_df.iterrows():
        user_idx = user_to_idx.get(row["user_id"])
        track_idx = track_to_idx.get(row["track_id"])

        if user_idx is None or track_idx is None:
            continue

        # Calculate implicit feedback score
        score = row["play_count"]

        # Boost for likes and saves
        if row["interaction_type"] == "like":
            score *= 1.5
        elif row["interaction_type"] == "save":
            score *= 2.0

        # Include rating if available
        if pd.notna(row.get("rating")):
            score *= row["rating"] / 3.0  # Normalize around 3

        rows.append(user_idx)
        cols.append(track_idx)
        data.append(score)

    matrix = sparse.csr_matrix(
        (data, (rows, cols)),
        shape=(len(user_ids), len(track_ids)),
    )

    return matrix


def generate_synthetic_data(
    dataset_path: str,
    n_users: int,
    interactions_per_user: int,
    output_dir: str,
    sample_tracks: int = None,
) -> dict:
    """
    Generate complete synthetic user interaction dataset.

    Args:
        dataset_path: Path to tracks CSV
        n_users: Number of synthetic users to create
        interactions_per_user: Average interactions per user
        output_dir: Directory to save output files
        sample_tracks: Optional limit on tracks to use (for faster testing)

    Returns:
        dict: Summary statistics
    """
    # Load tracks
    tracks_df = load_tracks(dataset_path)

    if sample_tracks and sample_tracks < len(tracks_df):
        # Sample tracks, preferring those with popularity data
        if "popularity" in tracks_df.columns:
            # Weighted sample by popularity
            weights = tracks_df["popularity"].fillna(0) + 1
            tracks_df = tracks_df.sample(n=sample_tracks, weights=weights)
        else:
            tracks_df = tracks_df.sample(n=sample_tracks)
        logger.info(f"Sampled {len(tracks_df):,} tracks for faster processing")

    # Calculate popularity scores
    if "popularity" in tracks_df.columns:
        popularity_scores = tracks_df["popularity"].fillna(0).values / 100.0
    else:
        # Use random popularity if not available
        popularity_scores = np.random.beta(2, 5, len(tracks_df))

    # Normalize popularity
    popularity_scores = (popularity_scores - popularity_scores.min()) / (
        popularity_scores.max() - popularity_scores.min() + 1e-8
    )

    # Generate users
    logger.info(f"Generating {n_users:,} synthetic users...")
    archetypes = list(USER_ARCHETYPES.keys())
    archetype_weights = [USER_ARCHETYPES[a]["weight"] for a in archetypes]

    users = []
    for i in range(n_users):
        archetype = np.random.choice(archetypes, p=archetype_weights)
        user = generate_user_profile(archetype, i)
        users.append(user)

    # Generate interactions
    logger.info(f"Generating interactions (~{interactions_per_user} per user)...")
    all_interactions = []

    for i, user in enumerate(users):
        if (i + 1) % 100 == 0:
            logger.info(f"  Processed {i + 1}/{n_users} users...")

        interactions = generate_interactions(
            user, tracks_df, interactions_per_user, popularity_scores
        )
        all_interactions.extend(interactions)

    interactions_df = pd.DataFrame(all_interactions)
    logger.info(f"Generated {len(interactions_df):,} total interactions")

    # Build interaction matrix
    logger.info("Building interaction matrix...")
    user_ids = [u["user_id"] for u in users]
    track_ids = tracks_df["id"].tolist()

    interaction_matrix = build_interaction_matrix(interactions_df, user_ids, track_ids)

    # Save outputs
    os.makedirs(output_dir, exist_ok=True)

    # Save users
    users_path = os.path.join(output_dir, "synthetic_users.json")
    with open(users_path, "w") as f:
        json.dump(users, f, indent=2)
    logger.info(f"Saved users to {users_path}")

    # Save interactions
    interactions_path = os.path.join(output_dir, "synthetic_interactions.csv")
    interactions_df.to_csv(interactions_path, index=False)
    logger.info(f"Saved interactions to {interactions_path}")

    # Save interaction matrix
    matrix_path = os.path.join(output_dir, "interaction_matrix.npz")
    sparse.save_npz(matrix_path, interaction_matrix)
    logger.info(f"Saved interaction matrix to {matrix_path}")

    # Save track ID mapping
    track_mapping_path = os.path.join(output_dir, "track_id_mapping.json")
    with open(track_mapping_path, "w") as f:
        json.dump(track_ids, f)
    logger.info(f"Saved track mapping to {track_mapping_path}")

    # Summary statistics
    stats = {
        "n_users": n_users,
        "n_tracks": len(track_ids),
        "n_interactions": len(interactions_df),
        "avg_interactions_per_user": len(interactions_df) / n_users,
        "matrix_shape": list(interaction_matrix.shape),
        "matrix_density": interaction_matrix.nnz
        / (interaction_matrix.shape[0] * interaction_matrix.shape[1]),
        "interaction_types": interactions_df["interaction_type"]
        .value_counts()
        .to_dict(),
        "archetype_distribution": pd.Series([u["archetype"] for u in users])
        .value_counts()
        .to_dict(),
        "generated_at": datetime.now().isoformat(),
    }

    stats_path = os.path.join(output_dir, "generation_stats.json")
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)

    logger.info("\n" + "=" * 50)
    logger.info("GENERATION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"  Users:              {stats['n_users']:,}")
    logger.info(f"  Tracks:             {stats['n_tracks']:,}")
    logger.info(f"  Interactions:       {stats['n_interactions']:,}")
    logger.info(f"  Avg per user:       {stats['avg_interactions_per_user']:.1f}")
    logger.info(f"  Matrix density:     {stats['matrix_density']:.6f}")
    logger.info("=" * 50)

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic user interaction data"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/processed/tracks.csv",
        help="Path to tracks CSV",
    )
    parser.add_argument(
        "--n-users",
        type=int,
        default=1000,
        help="Number of synthetic users (default: 1000)",
    )
    parser.add_argument(
        "--interactions-per-user",
        type=int,
        default=50,
        help="Average interactions per user (default: 50)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/synthetic",
        help="Output directory (default: data/synthetic)",
    )
    parser.add_argument(
        "--sample-tracks",
        type=int,
        default=None,
        help="Limit tracks for faster testing (default: use all)",
    )

    args = parser.parse_args()

    generate_synthetic_data(
        dataset_path=args.dataset,
        n_users=args.n_users,
        interactions_per_user=args.interactions_per_user,
        output_dir=args.output_dir,
        sample_tracks=args.sample_tracks,
    )


if __name__ == "__main__":
    main()
