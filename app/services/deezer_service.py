"""
Deezer API service for track previews.

Deezer provides free 30-second preview URLs without authentication.
"""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)


class DeezerService:
    """Service for interacting with Deezer API."""

    BASE_URL = "https://api.deezer.com"
    TIMEOUT = 10  # seconds

    def __init__(self):
        """Initialize Deezer service."""
        self.session = requests.Session()

    def search_track(
        self,
        query: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search for tracks on Deezer.

        Args:
            query: Search query (track name, artist, etc.)
            limit: Maximum number of results

        Returns:
            List of track results with preview URLs
        """
        try:
            url = f"{self.BASE_URL}/search/track"
            params = {
                "q": query,
                "limit": limit,
            }

            response = self.session.get(url, params=params, timeout=self.TIMEOUT)
            response.raise_for_status()

            data = response.json()
            tracks = data.get("data", [])

            return [self._format_track(track) for track in tracks]

        except requests.RequestException as e:
            logger.error(f"Deezer search error: {e}")
            return []

    def search_track_by_name_artist(
        self,
        track_name: str,
        artist_name: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Search for a specific track by name and artist.

        Args:
            track_name: Name of the track
            artist_name: Name of the artist

        Returns:
            Track info with preview URL or None if not found
        """
        # Build search query
        query = f'track:"{track_name}" artist:"{artist_name}"'
        results = self.search_track(query, limit=1)

        if results:
            return results[0]

        # Fallback to simpler query if exact search fails
        query = f"{track_name} {artist_name}"
        results = self.search_track(query, limit=3)

        # Find best match
        for track in results:
            track_title = track.get("title", "").lower()
            track_artist = track.get("artist", "").lower()

            if (
                track_name.lower() in track_title
                and artist_name.lower() in track_artist
            ):
                return track

        # Return first result if no exact match
        return results[0] if results else None

    def get_track_by_id(self, deezer_id: int) -> Optional[Dict[str, Any]]:
        """
        Get track info by Deezer ID.

        Args:
            deezer_id: Deezer track ID

        Returns:
            Track info with preview URL or None
        """
        try:
            url = f"{self.BASE_URL}/track/{deezer_id}"
            response = self.session.get(url, timeout=self.TIMEOUT)
            response.raise_for_status()

            data = response.json()

            if "error" in data:
                logger.warning(f"Deezer track not found: {deezer_id}")
                return None

            return self._format_track(data)

        except requests.RequestException as e:
            logger.error(f"Deezer get track error: {e}")
            return None

    def get_album_tracks(self, album_id: int) -> List[Dict[str, Any]]:
        """
        Get all tracks from an album.

        Args:
            album_id: Deezer album ID

        Returns:
            List of tracks with preview URLs
        """
        try:
            url = f"{self.BASE_URL}/album/{album_id}/tracks"
            response = self.session.get(url, timeout=self.TIMEOUT)
            response.raise_for_status()

            data = response.json()
            tracks = data.get("data", [])

            return [self._format_track(track) for track in tracks]

        except requests.RequestException as e:
            logger.error(f"Deezer album tracks error: {e}")
            return []

    def get_artist_top_tracks(
        self,
        artist_id: int,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get top tracks for an artist.

        Args:
            artist_id: Deezer artist ID
            limit: Maximum number of tracks

        Returns:
            List of top tracks with preview URLs
        """
        try:
            url = f"{self.BASE_URL}/artist/{artist_id}/top"
            params = {"limit": limit}
            response = self.session.get(url, params=params, timeout=self.TIMEOUT)
            response.raise_for_status()

            data = response.json()
            tracks = data.get("data", [])

            return [self._format_track(track) for track in tracks]

        except requests.RequestException as e:
            logger.error(f"Deezer artist top tracks error: {e}")
            return []

    def search_artist(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for artists on Deezer.

        Args:
            query: Artist name to search
            limit: Maximum number of results

        Returns:
            List of artist results
        """
        try:
            url = f"{self.BASE_URL}/search/artist"
            params = {"q": query, "limit": limit}
            response = self.session.get(url, params=params, timeout=self.TIMEOUT)
            response.raise_for_status()

            data = response.json()
            artists = data.get("data", [])

            return [
                {
                    "deezer_id": artist.get("id"),
                    "name": artist.get("name"),
                    "picture": artist.get("picture_medium"),
                    "picture_small": artist.get("picture_small"),
                    "picture_large": artist.get("picture_xl"),
                    "nb_fans": artist.get("nb_fan"),
                }
                for artist in artists
            ]

        except requests.RequestException as e:
            logger.error(f"Deezer artist search error: {e}")
            return []

    def _format_track(self, track: Dict[str, Any]) -> Dict[str, Any]:
        """Format Deezer track data to standard format."""
        artist = track.get("artist", {})
        album = track.get("album", {})

        return {
            "deezer_id": track.get("id"),
            "title": track.get("title"),
            "title_short": track.get("title_short"),
            "artist": artist.get("name") if isinstance(artist, dict) else artist,
            "artist_id": artist.get("id") if isinstance(artist, dict) else None,
            "album": album.get("title") if isinstance(album, dict) else album,
            "album_id": album.get("id") if isinstance(album, dict) else None,
            "duration": track.get("duration"),  # in seconds
            "preview_url": track.get("preview"),  # 30-second MP3 preview
            "cover_small": album.get("cover_small")
            if isinstance(album, dict)
            else None,
            "cover_medium": album.get("cover_medium")
            if isinstance(album, dict)
            else None,
            "cover_large": album.get("cover_xl") if isinstance(album, dict) else None,
            "explicit": track.get("explicit_lyrics", False),
            "rank": track.get("rank"),
        }


# Singleton instance
_deezer_service: Optional[DeezerService] = None


def get_deezer_service() -> DeezerService:
    """Get the singleton Deezer service instance."""
    global _deezer_service
    if _deezer_service is None:
        _deezer_service = DeezerService()
    return _deezer_service
