"""
Train/Test/Validation split utilities for recommendation system evaluation
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)


def create_interaction_splits(
    interactions_df: pd.DataFrame,
    test_size: float = 0.1,
    val_size: float = 0.1,
    random_state: int = 42,
    min_interactions_per_user: int = 5,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split user-item interactions into train/test/validation sets.

    Uses time-based or random splitting per user to avoid data leakage.

    Args:
        interactions_df: DataFrame with columns ['user_id', 'track_id', 'rating'/'play_count']
        test_size: Fraction of data for test set
        val_size: Fraction of data for validation set
        random_state: Random seed for reproducibility
        min_interactions_per_user: Minimum interactions needed to include user

    Returns:
        Tuple of (train_df, val_df, test_df)
    """
    np.random.seed(random_state)

    # Filter users with minimum interactions
    user_counts = interactions_df["user_id"].value_counts()
    valid_users = user_counts[user_counts >= min_interactions_per_user].index
    filtered_df = interactions_df[interactions_df["user_id"].isin(valid_users)].copy()

    logger.info(
        f"Users with >= {min_interactions_per_user} interactions: {len(valid_users)}"
    )
    logger.info(f"Total interactions after filtering: {len(filtered_df)}")

    train_list, val_list, test_list = [], [], []

    # Split per user to ensure each user has data in all sets
    for user_id, user_data in filtered_df.groupby("user_id"):
        n_interactions = len(user_data)

        if n_interactions < 3:
            # Not enough to split, put all in training
            train_list.append(user_data)
            continue

        # Shuffle user's interactions
        user_data = user_data.sample(frac=1, random_state=random_state)

        n_test = max(1, int(n_interactions * test_size))
        n_val = max(1, int(n_interactions * val_size))
        n_train = n_interactions - n_test - n_val

        if n_train < 1:
            n_train = 1
            n_test = max(1, (n_interactions - 1) // 2)
            n_val = n_interactions - n_train - n_test

        train_list.append(user_data.iloc[:n_train])
        val_list.append(user_data.iloc[n_train : n_train + n_val])
        test_list.append(user_data.iloc[n_train + n_val :])

    train_df = (
        pd.concat(train_list, ignore_index=True) if train_list else pd.DataFrame()
    )
    val_df = pd.concat(val_list, ignore_index=True) if val_list else pd.DataFrame()
    test_df = pd.concat(test_list, ignore_index=True) if test_list else pd.DataFrame()

    logger.info(
        f"Split sizes - Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}"
    )

    return train_df, val_df, test_df


def create_track_splits(
    tracks_df: pd.DataFrame,
    test_size: float = 0.1,
    val_size: float = 0.1,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split track dataset for content-based model evaluation.

    Args:
        tracks_df: DataFrame with track features
        test_size: Fraction for test set
        val_size: Fraction for validation set
        random_state: Random seed

    Returns:
        Tuple of (train_df, val_df, test_df)
    """
    # First split: separate test set
    train_val_df, test_df = train_test_split(
        tracks_df, test_size=test_size, random_state=random_state
    )

    # Second split: separate validation from training
    val_ratio = val_size / (1 - test_size)
    train_df, val_df = train_test_split(
        train_val_df, test_size=val_ratio, random_state=random_state
    )

    logger.info(
        f"Track split sizes - Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}"
    )

    return train_df, val_df, test_df


def get_user_ground_truth(
    test_df: pd.DataFrame, min_rating: Optional[float] = None
) -> Dict[str, List[str]]:
    """
    Extract ground truth (relevant items) per user from test set.

    Args:
        test_df: Test DataFrame with user_id, track_id columns
        min_rating: Minimum rating to consider as relevant (if rating column exists)

    Returns:
        Dict mapping user_id to list of relevant track_ids
    """
    ground_truth = {}

    for user_id, user_data in test_df.groupby("user_id"):
        if min_rating is not None and "rating" in user_data.columns:
            relevant = user_data[user_data["rating"] >= min_rating]["track_id"].tolist()
        else:
            relevant = user_data["track_id"].tolist()

        if relevant:
            ground_truth[user_id] = relevant

    return ground_truth
