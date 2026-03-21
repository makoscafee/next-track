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
        Get audio features for a track by its Spotify/dataset ID.
        ---
        tags:
          - Tracks
        parameters:
          - in: path
            name: track_id
            type: string
            required: true
            description: Spotify track ID
            example: 4u7EnebtmKWzUH433cf5Qv
        responses:
          200:
            description: Track info and audio features
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: success
                track:
                  type: object
                  properties:
                    id:
                      type: string
                    name:
                      type: string
                    artist:
                      type: string
                    album:
                      type: string
                audio_features:
                  type: object
                  properties:
                    danceability:
                      type: number
                    energy:
                      type: number
                    valence:
                      type: number
                    tempo:
                      type: number
                    acousticness:
                      type: number
                    instrumentalness:
                      type: number
                    speechiness:
                      type: number
          404:
            description: Track not found
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
        ---
        tags:
          - Tracks
        parameters:
          - in: query
            name: q
            type: string
            required: true
            description: Search query (track name or artist)
            example: Bohemian Rhapsody
          - in: query
            name: limit
            type: integer
            default: 10
            maximum: 50
          - in: query
            name: offset
            type: integer
            default: 0
            description: Pagination offset
          - in: query
            name: source
            type: string
            enum: [dataset, lastfm, both]
            default: both
          - in: query
            name: exclude_explicit
            type: boolean
            default: false
        responses:
          200:
            description: Search results
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: success
                results:
                  type: array
                  items:
                    type: object
                    properties:
                      name:
                        type: string
                      artist:
                        type: string
                      track_id:
                        type: string
                      explicit:
                        type: boolean
                      source:
                        type: string
                      has_audio_features:
                        type: boolean
                metadata:
                  type: object
                  properties:
                    query:
                      type: string
                    count:
                      type: integer
                    total:
                      type: integer
                    offset:
                      type: integer
                    limit:
                      type: integer
                    has_more:
                      type: boolean
          400:
            description: Missing query parameter q
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
        Get detailed track info including tags and dataset audio features.
        ---
        tags:
          - Tracks
        parameters:
          - in: query
            name: artist
            type: string
            required: true
            example: Queen
          - in: query
            name: track
            type: string
            required: true
            example: Bohemian Rhapsody
        responses:
          200:
            description: Track detail with optional audio features
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: success
                track_info:
                  type: object
                  properties:
                    name:
                      type: string
                    artist:
                      type: string
                    album:
                      type: string
                    duration_ms:
                      type: integer
                    listeners:
                      type: integer
                    playcount:
                      type: integer
                    url:
                      type: string
                tags:
                  type: array
                  items:
                    type: string
                audio_features:
                  type: object
                in_dataset:
                  type: boolean
          400:
            description: Missing artist or track parameter
          404:
            description: Track not found
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
        Get 30-second Deezer preview URL for a track.
        ---
        tags:
          - Tracks
        parameters:
          - in: query
            name: artist
            type: string
            required: true
            example: Queen
          - in: query
            name: track
            type: string
            required: true
            example: Bohemian Rhapsody
        responses:
          200:
            description: Deezer preview data
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: success
                preview:
                  type: object
                  properties:
                    deezer_id:
                      type: integer
                    title:
                      type: string
                    artist:
                      type: string
                    album:
                      type: string
                    preview_url:
                      type: string
                      description: 30-second MP3 preview URL
                    cover_small:
                      type: string
                    cover_medium:
                      type: string
                    cover_large:
                      type: string
                    duration:
                      type: integer
          400:
            description: Missing artist or track parameter
          404:
            description: Track not found on Deezer
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
        Search Deezer for tracks with 30-second preview URLs.
        ---
        tags:
          - Tracks
        parameters:
          - in: query
            name: q
            type: string
            required: true
            description: Search query
            example: Bohemian Rhapsody
          - in: query
            name: limit
            type: integer
            default: 10
            maximum: 25
        responses:
          200:
            description: Deezer search results with preview URLs
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: success
                results:
                  type: array
                  items:
                    type: object
                    properties:
                      deezer_id:
                        type: integer
                      title:
                        type: string
                      artist:
                        type: string
                      preview_url:
                        type: string
                      cover_medium:
                        type: string
                count:
                  type: integer
          400:
            description: Missing query parameter q
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
