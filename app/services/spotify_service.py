"""
Spotify API integration service
"""

import os

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


class SpotifyService:
    """Service for interacting with Spotify API."""

    def __init__(self):
        """Initialize Spotify client."""
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        if client_id and client_secret:
            auth_manager = SpotifyClientCredentials(
                client_id=client_id, client_secret=client_secret
            )
            self.client = spotipy.Spotify(auth_manager=auth_manager)
        else:
            self.client = None

    def get_audio_features(self, track_id):
        """
        Get audio features for a track.

        Args:
            track_id: Spotify track ID

        Returns:
            dict: Audio features or None if not available
        """
        if not self.client:
            return None

        try:
            features = self.client.audio_features([track_id])
            return features[0] if features else None
        except Exception as e:
            print(f"Error fetching audio features: {e}")
            return None

    def get_audio_features_batch(self, track_ids):
        """
        Get audio features for multiple tracks.

        Args:
            track_ids: List of Spotify track IDs (max 100)

        Returns:
            list: Audio features for each track
        """
        if not self.client:
            return []

        try:
            return self.client.audio_features(track_ids[:100])
        except Exception as e:
            print(f"Error fetching batch audio features: {e}")
            return []

    def get_track(self, track_id):
        """
        Get track metadata.

        Args:
            track_id: Spotify track ID

        Returns:
            dict: Track metadata
        """
        if not self.client:
            return None

        try:
            return self.client.track(track_id)
        except Exception as e:
            print(f"Error fetching track: {e}")
            return None

    def search_tracks(self, query, limit=10):
        """
        Search for tracks.

        Args:
            query: Search query
            limit: Number of results

        Returns:
            list: List of tracks
        """
        if not self.client:
            return []

        try:
            results = self.client.search(q=query, type="track", limit=limit)
            return results.get("tracks", {}).get("items", [])
        except Exception as e:
            print(f"Error searching tracks: {e}")
            return []

    def get_recommendations(
        self, seed_tracks=None, seed_artists=None, seed_genres=None, limit=10, **kwargs
    ):
        """
        Get Spotify recommendations.

        Args:
            seed_tracks: List of track IDs (max 5 total seeds)
            seed_artists: List of artist IDs
            seed_genres: List of genres
            limit: Number of recommendations
            **kwargs: Additional parameters (target_valence, target_energy, etc.)

        Returns:
            list: Recommended tracks
        """
        if not self.client:
            return []

        try:
            results = self.client.recommendations(
                seed_tracks=seed_tracks,
                seed_artists=seed_artists,
                seed_genres=seed_genres,
                limit=limit,
                **kwargs,
            )
            return results.get("tracks", [])
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return []
