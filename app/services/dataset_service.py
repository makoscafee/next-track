"""
Dataset service for loading and managing Kaggle Spotify dataset
Provides audio features that Last.fm doesn't offer
"""

import ast
import logging
import os
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.ml.data_quality import ALL_AUDIO_FEATURES, DataPreprocessor

logger = logging.getLogger(__name__)


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

    AUDIO_FEATURES = ALL_AUDIO_FEATURES

    def __init__(self, dataset_path: Optional[str] = None, artists_path: Optional[str] = None):
        """
        Initialize dataset service.

        Args:
            dataset_path: Path to the CSV dataset file
            artists_path: Path to the artists CSV file (for genre enrichment)
        """
        self.dataset_path = dataset_path or os.getenv(
            "DATASET_PATH", "data/processed/tracks.csv"
        )
        self.artists_path = artists_path or os.getenv(
            "ARTISTS_PATH", "data/processed/artists.csv"
        )
        self.tracks_df: Optional[pd.DataFrame] = None
        self._loaded = False
        self._quality_report: Optional[Dict] = None

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
            logger.warning(f"Dataset not found at {self.dataset_path}")
            return False

        try:
            logger.info(f"Loading dataset from {self.dataset_path}...")
            self.tracks_df = pd.read_csv(self.dataset_path)

            # Standardize column names (handle different dataset formats)
            self._standardize_columns()

            # Clean data
            self._clean_data()

            # Enrich with genre data from artists.csv
            self._enrich_genres()

            self._loaded = True
            logger.info(f"Loaded {len(self.tracks_df)} tracks")
            return True
        except Exception as e:
            logger.error(f"Error loading dataset: {e}")
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
        """Clean and preprocess the dataset using the data quality pipeline."""
        preprocessor = DataPreprocessor(
            features=self.AUDIO_FEATURES,
            max_missing_features=None,  # Keep all tracks for serving
            handle_outliers=False,  # Light cleaning only
        )
        self.tracks_df, self._quality_report = preprocessor.preprocess(
            self.tracks_df, validate=True
        )

    def _enrich_genres(self):
        """Enrich tracks with genre data from artists.csv."""
        if not os.path.exists(self.artists_path):
            logger.info("Artists file not found, skipping genre enrichment")
            return

        if "id_artists" not in self.tracks_df.columns:
            logger.info("No id_artists column, skipping genre enrichment")
            return

        try:
            logger.info("Enriching tracks with genre data...")
            artists_df = pd.read_csv(
                self.artists_path, usecols=["id", "genres"]
            )

            # Build artist_id -> genres lookup (only artists with genres)
            artists_with_genres = artists_df[artists_df["genres"] != "[]"]
            genre_lookup = {}
            for _, row in artists_with_genres.iterrows():
                try:
                    genres = ast.literal_eval(row["genres"])
                    if isinstance(genres, list) and genres:
                        genre_lookup[row["id"]] = genres
                except (ValueError, SyntaxError):
                    continue

            logger.info(f"Built genre lookup for {len(genre_lookup)} artists")

            # Map track -> genres via id_artists
            def _get_track_genres(id_artists_str):
                try:
                    artist_ids = ast.literal_eval(id_artists_str)
                    if not isinstance(artist_ids, list):
                        return []
                    genres = []
                    for aid in artist_ids:
                        genres.extend(genre_lookup.get(aid, []))
                    return list(set(genres))  # deduplicate
                except (ValueError, SyntaxError):
                    return []

            self.tracks_df["genres"] = self.tracks_df["id_artists"].apply(
                _get_track_genres
            )

            tracks_with_genres = (self.tracks_df["genres"].str.len() > 0).sum()
            logger.info(
                f"Genre enrichment complete: {tracks_with_genres} tracks "
                f"({100 * tracks_with_genres / len(self.tracks_df):.1f}%) have genres"
            )

        except Exception as e:
            logger.warning(f"Genre enrichment failed: {e}")
            if "genres" not in self.tracks_df.columns:
                self.tracks_df["genres"] = [[] for _ in range(len(self.tracks_df))]

    def get_tracks_by_genre(
        self,
        genres: List[str],
        limit: int = 20,
        exclude_explicit: bool = False,
    ) -> List[Dict]:
        """
        Get tracks matching any of the specified genres, ranked by popularity.

        Args:
            genres: List of genre keywords to match (e.g. ["rock", "jazz"])
            limit: Maximum results
            exclude_explicit: Filter out explicit tracks

        Returns:
            list: Matching tracks sorted by popularity
        """
        if not self._loaded:
            self.load_dataset()

        if self.tracks_df is None or "genres" not in self.tracks_df.columns:
            return []

        genres_lower = [g.lower().strip() for g in genres]

        # Match tracks where any genre contains any of the query terms
        def _matches_genre(track_genres):
            if not isinstance(track_genres, list) or not track_genres:
                return False
            for tg in track_genres:
                tg_lower = tg.lower()
                for query in genres_lower:
                    if query in tg_lower:
                        return True
            return False

        mask = self.tracks_df["genres"].apply(_matches_genre)

        if exclude_explicit and "explicit" in self.tracks_df.columns:
            mask = mask & (self.tracks_df["explicit"] != 1)

        matched = self.tracks_df[mask]

        if matched.empty:
            return []

        # Rank by popularity
        if "popularity" in matched.columns:
            matched = matched.sort_values("popularity", ascending=False)

        return matched.head(limit).to_dict("records")

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

    def search_tracks(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
        exclude_explicit: bool = False,
    ) -> Tuple[List[Dict], int]:
        """
        Search tracks by name or artist with pagination.

        Args:
            query: Search query
            limit: Maximum results
            offset: Number of results to skip
            exclude_explicit: Filter out explicit tracks

        Returns:
            tuple: (matching tracks list, total match count)
        """
        if not self._loaded:
            self.load_dataset()

        if self.tracks_df is None:
            return [], 0

        query_lower = query.lower()

        # Search in name and artists
        mask = self.tracks_df["name"].str.lower().str.contains(
            query_lower, na=False
        ) | self.tracks_df["artists"].str.lower().str.contains(query_lower, na=False)

        if exclude_explicit and "explicit" in self.tracks_df.columns:
            mask = mask & (self.tracks_df["explicit"] != 1)

        matched = self.tracks_df[mask]
        total = len(matched)
        results = matched.iloc[offset : offset + limit]
        return results.to_dict("records"), total

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

        return stats
