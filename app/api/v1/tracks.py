"""
Track features API endpoints
"""

from flask import request
from flask_restful import Resource

from app.extensions import cache
from app.services import DatasetService, LastFMService
from app.services.deezer_service import get_deezer_service

# Initialize services
dataset_service = DatasetService()
lastfm_service = LastFMService()


class TrackFeaturesResource(Resource):
    """Get audio features and info for a track."""

    def get(self, track_id):
        """
        Get audio features for a specific track by ID.

        Args:
            track_id: Track ID from dataset

        Returns:
        {
            "status": "success",
            "track": {...},
            "audio_features": {...}
        }
        """
        # Load dataset if needed
        dataset_service.load_dataset()

        # Get track from dataset
        track = dataset_service.get_track_by_id(track_id)

        if not track:
            return {
                "status": "error",
                "message": f'Track with ID "{track_id}" not found in dataset',
            }, 404

        # Get audio features
        audio_features = dataset_service.get_audio_features(track_id)

        return {
            "status": "success",
            "track": {
                "id": track.get("id"),
                "name": track.get("name"),
                "artist": track.get("artists"),
                "album": track.get("album"),
            },
            "audio_features": audio_features,
        }, 200


class TrackSearchResource(Resource):
    """Search for tracks."""

    @cache.cached(timeout=300, query_string=True)
    def get(self):
        """
        Search for tracks by name or artist.

        Query params:
            q: Search query
            limit: Max results (default 10, max 50)
            offset: Results to skip for pagination (default 0)
            source: 'dataset', 'lastfm', or 'both' (default 'both')
            exclude_explicit: Filter explicit tracks (default false)

        Returns:
        {
            "status": "success",
            "results": [...],
            "metadata": {
                "query": str,
                "count": int,
                "total": int,
                "offset": int,
                "limit": int,
                "has_more": bool,
                "source": str
            }
        }
        """
        query = request.args.get("q", "")
        limit = min(int(request.args.get("limit", 10)), 50)
        offset = max(int(request.args.get("offset", 0)), 0)
        source = request.args.get("source", "both")
        exclude_explicit = request.args.get("exclude_explicit", "false").lower() in (
            "true",
            "1",
            "yes",
        )

        if not query:
            return {
                "status": "error",
                "message": 'Query parameter "q" is required',
            }, 400

        results = []
        total = 0

        # Search dataset
        if source in ("dataset", "both"):
            dataset_service.load_dataset()
            dataset_results, dataset_total = dataset_service.search_tracks(
                query,
                limit=limit,
                offset=offset,
                exclude_explicit=exclude_explicit,
            )
            total += dataset_total
            for track in dataset_results:
                results.append(
                    {
                        "name": track.get("name"),
                        "artist": track.get("artists"),
                        "track_id": track.get("id"),
                        "explicit": bool(track.get("explicit", False)),
                        "source": "dataset",
                        "has_audio_features": True,
                    }
                )

        # Search Last.fm (no offset support — always fetches from start)
        if source in ("lastfm", "both"):
            lastfm_results = lastfm_service.search_tracks(query, limit=limit)
            for track in lastfm_results:
                results.append(
                    {
                        "name": track.get("name"),
                        "artist": track.get("artist"),
                        "listeners": track.get("listeners"),
                        "url": track.get("url"),
                        "source": "lastfm",
                        "has_audio_features": False,
                    }
                )

        count = len(results)
        has_more = (offset + count) < total if source in ("dataset",) else False

        return {
            "status": "success",
            "results": results,
            "metadata": {
                "query": query,
                "count": count,
                "total": total,
                "offset": offset,
                "limit": limit,
                "has_more": has_more,
                "source": source,
            },
        }, 200


class TrackInfoResource(Resource):
    """Get detailed track info from Last.fm."""

    @cache.cached(timeout=300, query_string=True)
    def get(self):
        """
        Get detailed track information from Last.fm.

        Query params:
            artist: Artist name
            track: Track name

        Returns:
        {
            "status": "success",
            "track_info": {...},
            "tags": [...],
            "similar_tracks": [...]
        }
        """
        artist = request.args.get("artist")
        track = request.args.get("track")

        if not artist or not track:
            return {
                "status": "error",
                "message": 'Both "artist" and "track" query parameters are required',
            }, 400

        # Get track info from Last.fm
        track_info = lastfm_service.get_track_info(artist, track)

        if not track_info:
            return {
                "status": "error",
                "message": f'Track "{track}" by "{artist}" not found on Last.fm',
            }, 404

        # Get tags
        tags = lastfm_service.get_track_tags(artist, track)

        # Try to get audio features from dataset
        dataset_service.load_dataset()
        dataset_track = dataset_service.get_track_by_name(track, artist)
        audio_features = None
        if dataset_track:
            audio_features = dataset_service.get_audio_features(dataset_track.get("id"))

        return {
            "status": "success",
            "track_info": {
                "name": track_info.get("name"),
                "artist": track_info.get("artist", {}).get("name")
                if isinstance(track_info.get("artist"), dict)
                else artist,
                "album": track_info.get("album", {}).get("title")
                if track_info.get("album")
                else None,
                "duration_ms": int(track_info.get("duration", 0)),
                "listeners": int(track_info.get("listeners", 0)),
                "playcount": int(track_info.get("playcount", 0)),
                "url": track_info.get("url"),
            },
            "tags": tags[:10],  # Top 10 tags
            "audio_features": audio_features,
            "in_dataset": dataset_track is not None,
        }, 200


class TrackPreviewResource(Resource):
    """Get track preview URL from Deezer."""

    def get(self):
        """
        Get 30-second preview URL for a track from Deezer.

        Query params:
            artist: Artist name
            track: Track name

        Returns:
        {
            "status": "success",
            "preview": {...}
        }
        """
        artist = request.args.get("artist")
        track = request.args.get("track")

        if not artist or not track:
            return {
                "status": "error",
                "message": 'Both "artist" and "track" query parameters are required',
            }, 400

        deezer = get_deezer_service()
        result = deezer.search_track_by_name_artist(track, artist)

        if not result:
            return {
                "status": "error",
                "message": f'Track "{track}" by "{artist}" not found on Deezer',
            }, 404

        return {
            "status": "success",
            "preview": {
                "deezer_id": result.get("deezer_id"),
                "title": result.get("title"),
                "artist": result.get("artist"),
                "album": result.get("album"),
                "preview_url": result.get("preview_url"),
                "cover_small": result.get("cover_small"),
                "cover_medium": result.get("cover_medium"),
                "cover_large": result.get("cover_large"),
                "duration": result.get("duration"),
            },
        }, 200


class TrackPreviewSearchResource(Resource):
    """Search for tracks with preview URLs."""

    @cache.cached(timeout=300, query_string=True)
    def get(self):
        """
        Search for tracks on Deezer (includes preview URLs).

        Query params:
            q: Search query
            limit: Max results (default 10, max 25)

        Returns:
        {
            "status": "success",
            "results": [...],
            "count": int
        }
        """
        query = request.args.get("q", "")
        limit = min(int(request.args.get("limit", 10)), 25)

        if not query:
            return {
                "status": "error",
                "message": 'Query parameter "q" is required',
            }, 400

        deezer = get_deezer_service()
        results = deezer.search_track(query, limit=limit)

        return {
            "status": "success",
            "results": results,
            "count": len(results),
        }, 200
