"""
Dataset service for loading and managing Kaggle Spotify dataset
Provides audio features that Last.fm doesn't offer
"""

import os
import pandas as pd
import numpy as np
from typing import Optional, List, Dict


class DatasetService:
    """
    Service for managing the Kaggle Spotify dataset.

    Expected dataset format (Kaggle Spotify 600K+ tracks):
    - id: Spotify track ID
    - name: Track name
    - artists: Artist name(s)
    - album: Album name
    - danceability, energy, valence, tempo, etc.: Audio features
    """

    AUDIO_FEATURES = [
        "danceability",
        "energy",
        "valence",
        "tempo",
        "acousticness",
        "instrumentalness",
        "speechiness",
        "liveness",
        "loudness",
        "key",
        "mode",
    ]

    def __init__(self, dataset_path: Optional[str] = None):
        """
        Initialize dataset service.

        Args:
            dataset_path: Path to the CSV dataset file
        """
        self.dataset_path = dataset_path or os.getenv(
            "DATASET_PATH", "data/processed/tracks.csv"
        )
        self.tracks_df: Optional[pd.DataFrame] = None
        self._loaded = False

    def load_dataset(self, force_reload: bool = False) -> bool:
        """
        Load the dataset from CSV.

        Args:
            force_reload: Force reload even if already loaded

        Returns:
            bool: True if loaded successfully
        """
        if self._loaded and not force_reload:
            return True

        if not os.path.exists(self.dataset_path):
            print(f"Dataset not found at {self.dataset_path}")
            print(
                "Please download the Kaggle Spotify dataset and place it in data/processed/"
            )
            return False

        try:
            print(f"Loading dataset from {self.dataset_path}...")
            self.tracks_df = pd.read_csv(self.dataset_path)

            # Standardize column names (handle different dataset formats)
            self._standardize_columns()

            # Clean data
            self._clean_data()

            self._loaded = True
            print(f"Loaded {len(self.tracks_df)} tracks")
            return True
        except Exception as e:
            print(f"Error loading dataset: {e}")
            return False

    def _standardize_columns(self):
        """Standardize column names across different dataset formats."""
        column_mapping = {
            "track_id": "id",
            "track_name": "name",
            "artist_name": "artists",
            "artist": "artists",
            "album_name": "album",
        }

        for old_name, new_name in column_mapping.items():
            if (
                old_name in self.tracks_df.columns
                and new_name not in self.tracks_df.columns
            ):
                self.tracks_df.rename(columns={old_name: new_name}, inplace=True)

    def _clean_data(self):
        """Clean and preprocess the dataset."""
        # Remove duplicates
        if "id" in self.tracks_df.columns:
            self.tracks_df.drop_duplicates(subset=["id"], inplace=True)

        # Handle missing values in audio features
        for feature in self.AUDIO_FEATURES:
            if feature in self.tracks_df.columns:
                self.tracks_df[feature].fillna(
                    self.tracks_df[feature].median(), inplace=True
                )

        # Normalize tempo to 0-1 scale if present
        if "tempo" in self.tracks_df.columns:
            max_tempo = self.tracks_df["tempo"].max()
            if max_tempo > 1:  # Not already normalized
                self.tracks_df["tempo_normalized"] = (
                    self.tracks_df["tempo"] / 250.0
                )  # Typical max ~250 BPM

    def get_track_by_id(self, track_id: str) -> Optional[Dict]:
        """
        Get track info by Spotify ID.

        Args:
            track_id: Spotify track ID

        Returns:
            dict: Track info with audio features
        """
        if not self._loaded:
            self.load_dataset()

        if self.tracks_df is None:
            return None

        track = self.tracks_df[self.tracks_df["id"] == track_id]
        if track.empty:
            return None

        return track.iloc[0].to_dict()

    def get_track_by_name(
        self, name: str, artist: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get track info by name and optionally artist.

        Args:
            name: Track name
            artist: Artist name (optional)

        Returns:
            dict: Track info with audio features
        """
        if not self._loaded:
            self.load_dataset()

        if self.tracks_df is None:
            return None

        # Case-insensitive search
        mask = self.tracks_df["name"].str.lower() == name.lower()

        if artist:
            artist_mask = (
                self.tracks_df["artists"]
                .str.lower()
                .str.contains(artist.lower(), na=False)
            )
            mask = mask & artist_mask

        tracks = self.tracks_df[mask]
        if tracks.empty:
            return None

        return tracks.iloc[0].to_dict()

    def search_tracks(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search tracks by name or artist.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            list: Matching tracks
        """
        if not self._loaded:
            self.load_dataset()

        if self.tracks_df is None:
            return []

        query_lower = query.lower()

        # Search in name and artists
        mask = self.tracks_df["name"].str.lower().str.contains(
            query_lower, na=False
        ) | self.tracks_df["artists"].str.lower().str.contains(query_lower, na=False)

        results = self.tracks_df[mask].head(limit)
        return results.to_dict("records")

    def get_audio_features(self, track_id: str) -> Optional[Dict]:
        """
        Get audio features for a track.

        Args:
            track_id: Spotify track ID

        Returns:
            dict: Audio features
        """
        track = self.get_track_by_id(track_id)
        if not track:
            return None

        return {
            feature: track.get(feature)
            for feature in self.AUDIO_FEATURES
            if feature in track
        }

    def get_features_dataframe(self) -> Optional[pd.DataFrame]:
        """
        Get dataframe with track IDs and audio features for ML models.

        Returns:
            DataFrame: Tracks with audio features
        """
        if not self._loaded:
            self.load_dataset()

        if self.tracks_df is None:
            return None

        # Select relevant columns
        columns = ["id", "name", "artists"] + [
            f for f in self.AUDIO_FEATURES if f in self.tracks_df.columns
        ]

        return self.tracks_df[columns].copy()

    def get_tracks_by_mood(
        self, valence_range: tuple, energy_range: tuple, limit: int = 20
    ) -> List[Dict]:
        """
        Get tracks matching mood parameters (valence and energy ranges).

        Args:
            valence_range: (min, max) valence values
            energy_range: (min, max) energy values
            limit: Maximum results

        Returns:
            list: Matching tracks
        """
        if not self._loaded:
            self.load_dataset()

        if self.tracks_df is None:
            return []

        mask = (
            (self.tracks_df["valence"] >= valence_range[0])
            & (self.tracks_df["valence"] <= valence_range[1])
            & (self.tracks_df["energy"] >= energy_range[0])
            & (self.tracks_df["energy"] <= energy_range[1])
        )

        results = (
            self.tracks_df[mask].sample(n=min(limit, mask.sum()))
            if mask.sum() > 0
            else pd.DataFrame()
        )
        return results.to_dict("records")

    def get_random_tracks(self, n: int = 10) -> List[Dict]:
        """
        Get random tracks from the dataset.

        Args:
            n: Number of tracks

        Returns:
            list: Random tracks
        """
        if not self._loaded:
            self.load_dataset()

        if self.tracks_df is None or len(self.tracks_df) == 0:
            return []

        sample_size = min(n, len(self.tracks_df))
        return self.tracks_df.sample(n=sample_size).to_dict("records")

    def get_statistics(self) -> Dict:
        """
        Get dataset statistics.

        Returns:
            dict: Dataset statistics
        """
        if not self._loaded:
            self.load_dataset()

        if self.tracks_df is None:
            return {"loaded": False}

        stats = {
            "loaded": True,
            "total_tracks": len(self.tracks_df),
            "unique_artists": self.tracks_df["artists"].nunique()
            if "artists" in self.tracks_df.columns
            else 0,
        }

        # Audio feature statistics
        for feature in self.AUDIO_FEATURES:
            if feature in self.tracks_df.columns:
                stats[f"{feature}_mean"] = float(self.tracks_df[feature].mean())
                stats[f"{feature}_std"] = float(self.tracks_df[feature].std())
                stats[f'{feature}_std'] = float(self.tracks_df[feature].std())

        return stats
