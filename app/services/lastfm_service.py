"""
Last.fm API integration service
"""

import hashlib
import os
from urllib.parse import urlencode

import requests


class LastFMService:
    """Service for interacting with Last.fm API."""

    BASE_URL = "http://ws.audioscrobbler.com/2.0/"

    def __init__(self):
        """Initialize Last.fm client."""
        self.api_key = os.getenv("LASTFM_API_KEY")
        self.api_secret = os.getenv("LASTFM_API_SECRET")
        self.session = requests.Session()

    def _make_request(self, method, **params):
        """
        Make a request to the Last.fm API.

        Args:
            method: API method name
            **params: Additional parameters

        Returns:
            dict: JSON response or None on error
        """
        if not self.api_key:
            print("Last.fm API key not configured")
            return None

        params["method"] = method
        params["api_key"] = self.api_key
        params["format"] = "json"

        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Check for API errors
            if "error" in data:
                print(f"Last.fm API error: {data.get('message', 'Unknown error')}")
                return None

            return data
        except requests.RequestException as e:
            print(f"Last.fm request error: {e}")
            return None

    # Track methods

    def get_track_info(self, artist, track):
        """
        Get detailed track information.

        Args:
            artist: Artist name
            track: Track name

        Returns:
            dict: Track info including tags, listeners, playcount
        """
        data = self._make_request("track.getInfo", artist=artist, track=track)
        return data.get("track") if data else None

    def get_similar_tracks(self, artist, track, limit=10):
        """
        Get tracks similar to a given track.

        Args:
            artist: Artist name
            track: Track name
            limit: Number of similar tracks

        Returns:
            list: Similar tracks with match scores
        """
        data = self._make_request(
            "track.getSimilar", artist=artist, track=track, limit=limit
        )

        if not data or "similartracks" not in data:
            return []

        similar = data["similartracks"].get("track", [])

        # Handle single track response (Last.fm returns dict instead of list)
        if isinstance(similar, dict):
            similar = [similar]

        return [
            {
                "name": t.get("name"),
                "artist": t.get("artist", {}).get("name")
                if isinstance(t.get("artist"), dict)
                else t.get("artist"),
                "match": float(t.get("match", 0)),
                "url": t.get("url"),
                "mbid": t.get("mbid"),
            }
            for t in similar
        ]

    def get_track_tags(self, artist, track):
        """
        Get top tags for a track.

        Args:
            artist: Artist name
            track: Track name

        Returns:
            list: Tags with counts
        """
        data = self._make_request("track.getTopTags", artist=artist, track=track)

        if not data or "toptags" not in data:
            return []

        tags = data["toptags"].get("tag", [])
        if isinstance(tags, dict):
            tags = [tags]

        return [
            {
                "name": t.get("name"),
                "count": int(t.get("count", 0)),
                "url": t.get("url"),
            }
            for t in tags
        ]

    def search_tracks(self, query, limit=10):
        """
        Search for tracks.

        Args:
            query: Search query
            limit: Number of results

        Returns:
            list: Matching tracks
        """
        data = self._make_request("track.search", track=query, limit=limit)

        if not data or "results" not in data:
            return []

        tracks = data["results"].get("trackmatches", {}).get("track", [])
        if isinstance(tracks, dict):
            tracks = [tracks]

        return [
            {
                "name": t.get("name"),
                "artist": t.get("artist"),
                "listeners": int(t.get("listeners", 0)),
                "url": t.get("url"),
                "mbid": t.get("mbid"),
            }
            for t in tracks
        ]

    # Artist methods

    def get_artist_info(self, artist):
        """
        Get artist information.

        Args:
            artist: Artist name

        Returns:
            dict: Artist info
        """
        data = self._make_request("artist.getInfo", artist=artist)
        return data.get("artist") if data else None

    def get_similar_artists(self, artist, limit=10):
        """
        Get artists similar to a given artist.

        Args:
            artist: Artist name
            limit: Number of similar artists

        Returns:
            list: Similar artists
        """
        data = self._make_request("artist.getSimilar", artist=artist, limit=limit)

        if not data or "similarartists" not in data:
            return []

        similar = data["similarartists"].get("artist", [])
        if isinstance(similar, dict):
            similar = [similar]

        return [
            {
                "name": a.get("name"),
                "match": float(a.get("match", 0)),
                "url": a.get("url"),
                "mbid": a.get("mbid"),
            }
            for a in similar
        ]

    def get_artist_top_tracks(self, artist, limit=10):
        """
        Get top tracks for an artist.

        Args:
            artist: Artist name
            limit: Number of tracks

        Returns:
            list: Top tracks
        """
        data = self._make_request("artist.getTopTracks", artist=artist, limit=limit)

        if not data or "toptracks" not in data:
            return []

        tracks = data["toptracks"].get("track", [])
        if isinstance(tracks, dict):
            tracks = [tracks]

        return [
            {
                "name": t.get("name"),
                "playcount": int(t.get("playcount", 0)),
                "listeners": int(t.get("listeners", 0)),
                "url": t.get("url"),
                "mbid": t.get("mbid"),
            }
            for t in tracks
        ]

    # Tag methods

    def get_tag_top_tracks(self, tag, limit=10):
        """
        Get top tracks for a tag/genre.

        Args:
            tag: Tag name (e.g., 'rock', 'happy', 'chill')
            limit: Number of tracks

        Returns:
            list: Top tracks for the tag
        """
        data = self._make_request("tag.getTopTracks", tag=tag, limit=limit)

        if not data or "tracks" not in data:
            return []

        tracks = data["tracks"].get("track", [])
        if isinstance(tracks, dict):
            tracks = [tracks]

        return [
            {
                "name": t.get("name"),
                "artist": t.get("artist", {}).get("name")
                if isinstance(t.get("artist"), dict)
                else t.get("artist"),
                "url": t.get("url"),
                "mbid": t.get("mbid"),
            }
            for t in tracks
        ]

    def get_tag_info(self, tag):
        """
        Get information about a tag.

        Args:
            tag: Tag name

        Returns:
            dict: Tag info
        """
        data = self._make_request("tag.getInfo", tag=tag)
        return data.get("tag") if data else None

    # Chart methods

    def get_chart_top_tracks(self, limit=50):
        """
        Get current top tracks chart.

        Args:
            limit: Number of tracks

        Returns:
            list: Chart top tracks
        """
        data = self._make_request("chart.getTopTracks", limit=limit)

        if not data or "tracks" not in data:
            return []

        tracks = data["tracks"].get("track", [])
        if isinstance(tracks, dict):
            tracks = [tracks]

        return [
            {
                "name": t.get("name"),
                "artist": t.get("artist", {}).get("name")
                if isinstance(t.get("artist"), dict)
                else t.get("artist"),
                "playcount": int(t.get("playcount", 0)),
                "listeners": int(t.get("listeners", 0)),
                "url": t.get("url"),
                "mbid": t.get("mbid"),
            }
            for t in tracks
        ]

    # User methods (requires user authentication for some)

    def get_user_top_tracks(self, user, period="overall", limit=10):
        """
        Get a user's top tracks.

        Args:
            user: Last.fm username
            period: Time period (overall, 7day, 1month, 3month, 6month, 12month)
            limit: Number of tracks

        Returns:
            list: User's top tracks
        """
        data = self._make_request(
            "user.getTopTracks", user=user, period=period, limit=limit
        )

        if not data or "toptracks" not in data:
            return []

        tracks = data["toptracks"].get("track", [])
        if isinstance(tracks, dict):
            tracks = [tracks]

        return [
            {
                "name": t.get("name"),
                "artist": t.get("artist", {}).get("name")
                if isinstance(t.get("artist"), dict)
                else t.get("artist"),
                "playcount": int(t.get("playcount", 0)),
                "url": t.get("url"),
                "mbid": t.get("mbid"),
            }
            for t in tracks
        ]

    def get_user_recent_tracks(self, user, limit=10):
        """
        Get a user's recently played tracks.

        Args:
            user: Last.fm username
            limit: Number of tracks

        Returns:
            list: Recently played tracks
        """
        data = self._make_request("user.getRecentTracks", user=user, limit=limit)

        if not data or "recenttracks" not in data:
            return []

        tracks = data["recenttracks"].get("track", [])
        if isinstance(tracks, dict):
            tracks = [tracks]

        return [
            {
                "name": t.get("name"),
                "artist": t.get("artist", {}).get("#text")
                if isinstance(t.get("artist"), dict)
                else t.get("artist"),
                "album": t.get("album", {}).get("#text")
                if isinstance(t.get("album"), dict)
                else t.get("album"),
                "url": t.get("url"),
                "now_playing": t.get("@attr", {}).get("nowplaying") == "true",
            }
            for t in tracks
        ]
