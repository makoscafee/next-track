"""
Spotify API integration service.
Replaces Last.fm for track discovery, similar tracks, charts, and metadata.
Uses Client Credentials flow (no user login required).
"""

import logging
import os
from typing import Dict, List, Optional

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

logger = logging.getLogger(__name__)

# Spotify's public Global Top 50 playlist
_GLOBAL_TOP_50_PLAYLIST_ID = "37i9dQZEVXbMDoHDwVN2tF"


class SpotifyService:
    """Service for interacting with the Spotify Web API."""

    def __init__(self):
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        if client_id and client_secret:
            auth_manager = SpotifyClientCredentials(
                client_id=client_id, client_secret=client_secret
            )
            self.client = spotipy.Spotify(auth_manager=auth_manager)
        else:
            logger.warning("Spotify client ID/secret not configured")
            self.client = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_track_id(self, track: str, artist: str) -> Optional[str]:
        """Search for a track and return its Spotify ID."""
        if not self.client:
            return None
        try:
            results = self.client.search(
                q=f"track:{track} artist:{artist}", type="track", limit=1
            )
            items = results.get("tracks", {}).get("items", [])
            return items[0]["id"] if items else None
        except Exception as e:
            logger.error(f"Error finding track ID for '{track}' by '{artist}': {e}")
            return None

    def _find_artist_id(self, artist: str) -> Optional[str]:
        """Search for an artist and return their Spotify ID."""
        if not self.client:
            return None
        try:
            results = self.client.search(q=f"artist:{artist}", type="artist", limit=1)
            items = results.get("artists", {}).get("items", [])
            return items[0]["id"] if items else None
        except Exception as e:
            logger.error(f"Error finding artist ID for '{artist}': {e}")
            return None

    def _format_track(self, item: Dict, match: float = 0.0) -> Dict:
        """Normalise a Spotify track object into our internal shape."""
        artists = item.get("artists", [])
        artist_name = artists[0]["name"] if artists else None
        return {
            "track_id": item.get("id"),   # Spotify ID — matches dataset directly
            "name": item.get("name"),
            "artist": artist_name,
            "album": item.get("album", {}).get("name"),
            "duration_ms": item.get("duration_ms"),
            "explicit": item.get("explicit", False),
            "popularity": item.get("popularity", 0),
            "url": item.get("external_urls", {}).get("spotify"),
            "match": match,
        }

    # ------------------------------------------------------------------
    # Track methods
    # ------------------------------------------------------------------

    def get_track_info(self, artist: str, track: str) -> Optional[Dict]:
        """
        Get detailed track information.

        Args:
            artist: Artist name
            track: Track name

        Returns:
            dict: Track info or None
        """
        if not self.client:
            return None
        track_id = self._find_track_id(track, artist)
        if not track_id:
            return None
        try:
            data = self.client.track(track_id)
            return self._format_track(data)
        except Exception as e:
            logger.error(f"Error fetching track info: {e}")
            return None

    def get_similar_tracks(self, artist: str, track: str, limit: int = 10) -> List[Dict]:
        """
        Get tracks similar to a given track via Spotify recommendations.

        Falls back to artist top tracks if the recommendations endpoint is
        unavailable (restricted for some developer accounts).

        Args:
            artist: Artist name
            track: Track name
            limit: Number of similar tracks

        Returns:
            list: Similar tracks
        """
        if not self.client:
            return []

        track_id = self._find_track_id(track, artist)
        if not track_id:
            return []

        try:
            results = self.client.recommendations(seed_tracks=[track_id], limit=limit)
            tracks = results.get("tracks", [])
            if tracks:
                return [self._format_track(t) for t in tracks]
        except Exception as e:
            logger.warning(f"Spotify recommendations unavailable: {e}")

        # Fallback: artist top tracks (excluding the seed track itself)
        logger.info("Falling back to artist top tracks for similarity")
        top = self.get_artist_top_tracks(artist, limit=limit + 1)
        return [t for t in top if t.get("track_id") != track_id][:limit]

    def get_track_tags(self, artist: str, track: str) -> List[Dict]:
        """
        Get genres for a track (via its primary artist).

        Spotify exposes artist-level genres rather than per-track user tags.

        Args:
            artist: Artist name
            track: Track name (kept for API compatibility with Last.fm interface)

        Returns:
            list: Genre dicts with 'name' and 'count' keys
        """
        if not self.client:
            return []

        artist_id = self._find_artist_id(artist)
        if not artist_id:
            return []

        try:
            data = self.client.artist(artist_id)
            return [{"name": g, "count": 100} for g in data.get("genres", [])]
        except Exception as e:
            logger.error(f"Error fetching artist genres: {e}")
            return []

    def get_audio_features(self, track_id: str) -> Optional[Dict]:
        """
        Get Spotify audio features for a track by ID.

        Supplements the local dataset — useful for tracks not in tracks.csv.

        Args:
            track_id: Spotify track ID

        Returns:
            dict: Audio features or None
        """
        if not self.client:
            return None
        try:
            features = self.client.audio_features([track_id])
            if not features or not features[0]:
                return None
            f = features[0]
            return {
                "danceability": f.get("danceability"),
                "energy": f.get("energy"),
                "valence": f.get("valence"),
                "tempo": f.get("tempo"),
                "acousticness": f.get("acousticness"),
                "instrumentalness": f.get("instrumentalness"),
                "speechiness": f.get("speechiness"),
                "liveness": f.get("liveness"),
                "loudness": f.get("loudness"),
                "key": f.get("key"),
                "mode": f.get("mode"),
            }
        except Exception as e:
            logger.error(f"Error fetching audio features for {track_id}: {e}")
            return None

    def get_audio_features_batch(self, track_ids: List[str]) -> List[Optional[Dict]]:
        """
        Get audio features for multiple tracks (max 100).

        Args:
            track_ids: List of Spotify track IDs

        Returns:
            list: Audio features for each track (None where unavailable)
        """
        if not self.client:
            return []
        try:
            return self.client.audio_features(track_ids[:100])
        except Exception as e:
            logger.error(f"Error fetching batch audio features: {e}")
            return []

    def search_tracks(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for tracks.

        Args:
            query: Search query
            limit: Number of results

        Returns:
            list: Matching tracks
        """
        if not self.client:
            return []
        try:
            results = self.client.search(q=query, type="track", limit=min(limit, 10))
            items = results.get("tracks", {}).get("items", [])
            return [self._format_track(t) for t in items]
        except Exception as e:
            logger.error(f"Error searching tracks: {e}")
            return []

    # ------------------------------------------------------------------
    # Artist methods
    # ------------------------------------------------------------------

    def get_artist_info(self, artist: str) -> Optional[Dict]:
        """
        Get artist information.

        Args:
            artist: Artist name

        Returns:
            dict: Artist info or None
        """
        if not self.client:
            return None
        artist_id = self._find_artist_id(artist)
        if not artist_id:
            return None
        try:
            return self.client.artist(artist_id)
        except Exception as e:
            logger.error(f"Error fetching artist info: {e}")
            return None

    def get_similar_artists(self, artist: str, limit: int = 10) -> List[Dict]:
        """
        Get artists similar to a given artist.

        Args:
            artist: Artist name
            limit: Number of similar artists

        Returns:
            list: Similar artists
        """
        if not self.client:
            return []
        artist_id = self._find_artist_id(artist)
        if not artist_id:
            return []
        try:
            data = self.client.artist_related_artists(artist_id)
            return [
                {
                    "name": a.get("name"),
                    "artist_id": a.get("id"),
                    "genres": a.get("genres", []),
                    "popularity": a.get("popularity", 0),
                    "url": a.get("external_urls", {}).get("spotify"),
                    "match": a.get("popularity", 0) / 100,
                }
                for a in data.get("artists", [])[:limit]
            ]
        except Exception as e:
            logger.error(f"Error fetching similar artists: {e}")
            return []

    def get_artist_top_tracks(self, artist: str, limit: int = 10) -> List[Dict]:
        """
        Get top tracks for an artist.

        Args:
            artist: Artist name
            limit: Number of tracks

        Returns:
            list: Top tracks
        """
        if not self.client:
            return []
        artist_id = self._find_artist_id(artist)
        if not artist_id:
            return []
        try:
            data = self.client.artist_top_tracks(artist_id)
            return [self._format_track(t) for t in data.get("tracks", [])[:limit]]
        except Exception as e:
            logger.error(f"Error fetching artist top tracks: {e}")
            return []

    # ------------------------------------------------------------------
    # Genre/tag methods
    # ------------------------------------------------------------------

    def get_tag_top_tracks(self, tag: str, limit: int = 10) -> List[Dict]:
        """
        Get top tracks for a genre/tag via Spotify recommendations.

        Falls back to a genre keyword search if the recommendations
        endpoint is unavailable.

        Args:
            tag: Genre name (e.g. 'rock', 'chill', 'jazz')
            limit: Number of tracks

        Returns:
            list: Top tracks for the genre
        """
        if not self.client:
            return []

        genre_seed = tag.lower().replace(" ", "-")

        try:
            results = self.client.recommendations(
                seed_genres=[genre_seed], limit=min(limit, 100)
            )
            tracks = results.get("tracks", [])
            if tracks:
                return [self._format_track(t) for t in tracks]
        except Exception as e:
            logger.warning(f"Spotify recommendations unavailable for genre '{tag}': {e}")

        # Fallback: search by genre keyword
        logger.info(f"Falling back to search for genre '{tag}'")
        return self.search_tracks(f"genre:{genre_seed}", limit=limit)

    # ------------------------------------------------------------------
    # Chart methods
    # ------------------------------------------------------------------

    def get_chart_top_tracks(self, limit: int = 50) -> List[Dict]:
        """
        Get current global top tracks via Spotify's Global Top 50 playlist.

        Args:
            limit: Number of tracks (max 50)

        Returns:
            list: Chart top tracks
        """
        if not self.client:
            return []
        try:
            data = self.client.playlist_tracks(
                _GLOBAL_TOP_50_PLAYLIST_ID,
                limit=min(limit, 50),
                fields="items(track(id,name,artists,album,duration_ms,explicit,popularity,external_urls))",
            )
            tracks = []
            for item in data.get("items", []):
                t = item.get("track")
                if t:
                    tracks.append(self._format_track(t))
            return tracks
        except Exception as e:
            logger.error(f"Error fetching chart top tracks: {e}")
            return []

    # ------------------------------------------------------------------
    # Recommendations (raw Spotify endpoint — used by recommendation.py)
    # ------------------------------------------------------------------

    def get_recommendations(
        self,
        seed_tracks: Optional[List[str]] = None,
        seed_artists: Optional[List[str]] = None,
        seed_genres: Optional[List[str]] = None,
        limit: int = 10,
        **kwargs,
    ) -> List[Dict]:
        """
        Get Spotify recommendations with optional audio feature targets.

        Args:
            seed_tracks: List of Spotify track IDs (up to 5 total seeds)
            seed_artists: List of Spotify artist IDs
            seed_genres: List of genre seeds
            limit: Number of recommendations
            **kwargs: Audio feature targets (target_valence, target_energy, etc.)

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
            return [self._format_track(t) for t in results.get("tracks", [])]
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []

    # ------------------------------------------------------------------
    # User methods (require OAuth — stubbed until OAuth flow is added)
    # ------------------------------------------------------------------

    def get_user_top_tracks(
        self, user: str, period: str = "overall", limit: int = 10
    ) -> List[Dict]:
        """
        Get a user's top tracks. Requires OAuth — not yet implemented.
        """
        logger.info("get_user_top_tracks requires OAuth — not yet implemented")
        return []

    def get_user_recent_tracks(self, user: str, limit: int = 10) -> List[Dict]:
        """
        Get a user's recently played tracks. Requires OAuth — not yet implemented.
        """
        logger.info("get_user_recent_tracks requires OAuth — not yet implemented")
        return []
