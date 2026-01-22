"""
Recommendation service - orchestrates the hybrid recommendation system
Combines Last.fm similarity data with Kaggle dataset audio features
"""

from typing import List, Dict, Optional

from app.services.lastfm_service import LastFMService
from app.services.dataset_service import DatasetService
from app.ml.hybrid import HybridRecommender


class RecommendationService:
    """Service for generating recommendations using Last.fm + dataset."""

    def __init__(self):
        """Initialize recommendation service."""
        self.lastfm = LastFMService()
        self.dataset = DatasetService()
        self.hybrid_model = HybridRecommender()
        self._models_initialized = False

    def initialize_models(self):
        """Initialize ML models with dataset."""
        if self._models_initialized:
            return True

        # Load dataset
        if not self.dataset.load_dataset():
            print("Warning: Dataset not loaded. Some features may be limited.")
            return False

        # Get features dataframe for ML models
        features_df = self.dataset.get_features_dataframe()
        if features_df is not None:
            # Rename 'id' to 'track_id' for ML models
            features_df = features_df.rename(columns={"id": "track_id"})

            # Fit content-based and sentiment models
            self.hybrid_model.fit_content(features_df)
            self.hybrid_model.fit_sentiment(features_df)
            self._models_initialized = True
            print("ML models initialized successfully")
            return True

        return False

    def get_recommendations(
        self,
        user_id: Optional[str] = None,
        seed_tracks: Optional[List[Dict]] = None,
        mood: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """
        Get hybrid recommendations combining Last.fm and dataset.

        Args:
            user_id: Optional user ID for personalized recommendations
            seed_tracks: List of seed tracks [{'name': str, 'artist': str}, ...]
            mood: Optional mood string (e.g., 'happy', 'sad', 'energetic')
            limit: Number of recommendations

        Returns:
            list: Recommended tracks with scores and metadata
        """
        recommendations = []

        # Strategy 1: Use Last.fm similar tracks if seed tracks provided
        if seed_tracks:
            lastfm_recs = self._get_lastfm_recommendations(seed_tracks, limit * 2)
            recommendations.extend(lastfm_recs)

        # Strategy 2: Use mood-based recommendations from dataset
        if mood:
            mood_recs = self._get_mood_recommendations(mood, limit)
            recommendations.extend(mood_recs)

        # Strategy 3: If we have dataset features, use content-based model
        if seed_tracks and self._models_initialized:
            content_recs = self._get_content_recommendations(seed_tracks, limit)
            recommendations.extend(content_recs)

        # Deduplicate and rank
        recommendations = self._deduplicate_and_rank(recommendations, limit)

        # Fallback to chart tracks if no recommendations
        if not recommendations:
            recommendations = self._get_fallback_recommendations(limit)

        return recommendations

    def _get_lastfm_recommendations(
        self, seed_tracks: List[Dict], limit: int
    ) -> List[Dict]:
        """Get recommendations from Last.fm similar tracks."""
        recommendations = []

        for seed in seed_tracks[:3]:  # Limit seed tracks
            name = seed.get("name")
            artist = seed.get("artist")

            if name and artist:
                similar = self.lastfm.get_similar_tracks(
                    artist, name, limit=limit // len(seed_tracks)
                )

                for track in similar:
                    # Try to enrich with dataset audio features
                    enriched = self._enrich_with_dataset(track)
                    enriched["source"] = "lastfm_similar"
                    enriched["seed_track"] = f"{name} by {artist}"
                    recommendations.append(enriched)

        return recommendations

    def _get_mood_recommendations(self, mood: str, limit: int) -> List[Dict]:
        """Get mood-based recommendations from dataset."""
        # Map mood to valence/energy ranges
        mood_mapping = {
            "happy": {"valence": (0.6, 1.0), "energy": (0.5, 1.0)},
            "sad": {"valence": (0.0, 0.4), "energy": (0.0, 0.5)},
            "energetic": {"valence": (0.4, 1.0), "energy": (0.7, 1.0)},
            "calm": {"valence": (0.3, 0.7), "energy": (0.0, 0.4)},
            "angry": {"valence": (0.0, 0.4), "energy": (0.7, 1.0)},
            "relaxed": {"valence": (0.5, 0.8), "energy": (0.1, 0.4)},
            "excited": {"valence": (0.6, 1.0), "energy": (0.7, 1.0)},
            "melancholic": {"valence": (0.2, 0.5), "energy": (0.2, 0.5)},
        }

        params = mood_mapping.get(
            mood.lower(), {"valence": (0.3, 0.7), "energy": (0.3, 0.7)}
        )

        tracks = self.dataset.get_tracks_by_mood(
            params["valence"], params["energy"], limit=limit
        )

        return [
            {
                "name": t.get("name"),
                "artist": t.get("artists"),
                "track_id": t.get("id"),
                "audio_features": {
                    "valence": t.get("valence"),
                    "energy": t.get("energy"),
                    "danceability": t.get("danceability"),
                    "tempo": t.get("tempo"),
                },
                "source": "mood_match",
                "mood": mood,
                "score": 0.7,
            }
            for t in tracks
        ]

    def _get_content_recommendations(
        self, seed_tracks: List[Dict], limit: int
    ) -> List[Dict]:
        """Get content-based recommendations using audio features."""
        if not self._models_initialized:
            return []

        recommendations = []

        for seed in seed_tracks[:2]:
            # Find seed track in dataset
            track_data = self.dataset.get_track_by_name(
                seed.get("name", ""), seed.get("artist")
            )

            if track_data:
                # Use content-based model
                seed_features = {
                    "danceability": track_data.get("danceability", 0.5),
                    "energy": track_data.get("energy", 0.5),
                    "valence": track_data.get("valence", 0.5),
                    "tempo": track_data.get("tempo", 120),
                    "acousticness": track_data.get("acousticness", 0.5),
                    "instrumentalness": track_data.get("instrumentalness", 0.5),
                    "speechiness": track_data.get("speechiness", 0.5),
                }

                content_recs = self.hybrid_model.content_model.recommend(
                    seed_features, n_recommendations=limit
                )

                for rec in content_recs:
                    track = self.dataset.get_track_by_id(rec["track_id"])
                    if track:
                        recommendations.append(
                            {
                                "name": track.get("name"),
                                "artist": track.get("artists"),
                                "track_id": rec["track_id"],
                                "score": rec["similarity_score"],
                                "source": "content_based",
                                "audio_features": self.dataset.get_audio_features(
                                    rec["track_id"]
                                ),
                            }
                        )

        return recommendations

    def _enrich_with_dataset(self, track: Dict) -> Dict:
        """Enrich Last.fm track with dataset audio features."""
        enriched = track.copy()

        # Try to find in dataset
        dataset_track = self.dataset.get_track_by_name(
            track.get("name", ""), track.get("artist")
        )

        if dataset_track:
            enriched["track_id"] = dataset_track.get("id")
            enriched["audio_features"] = self.dataset.get_audio_features(
                dataset_track.get("id")
            )
            enriched["in_dataset"] = True
        else:
            enriched["in_dataset"] = False

        # Convert match score to standard score
        if "match" in enriched:
            enriched["score"] = enriched["match"]

        return enriched

    def _deduplicate_and_rank(
        self, recommendations: List[Dict], limit: int
    ) -> List[Dict]:
        """Deduplicate recommendations and rank by score."""
        seen = set()
        unique = []

        for rec in recommendations:
            # Create unique key from name and artist
            key = f"{rec.get('name', '').lower()}_{rec.get('artist', '').lower()}"

            if key not in seen:
                seen.add(key)
                unique.append(rec)

        # Sort by score (descending)
        unique.sort(key=lambda x: x.get("score", 0), reverse=True)

        return unique[:limit]

    def _get_fallback_recommendations(self, limit: int) -> List[Dict]:
        """Get fallback recommendations when other methods fail."""
        # Try Last.fm charts
        chart_tracks = self.lastfm.get_chart_top_tracks(limit=limit)

        if chart_tracks:
            return [
                {
                    "name": t.get("name"),
                    "artist": t.get("artist"),
                    "source": "chart",
                    "playcount": t.get("playcount"),
                    "score": 0.5,
                }
                for t in chart_tracks
            ]

        # Fallback to random dataset tracks
        return [
            {
                "name": t.get("name"),
                "artist": t.get("artists"),
                "track_id": t.get("id"),
                "source": "random",
                "score": 0.3,
            }
            for t in self.dataset.get_random_tracks(limit)
        ]

    def get_similar_tracks(
        self, artist: str, track: str, limit: int = 10
    ) -> List[Dict]:
        """
        Find tracks similar to a given track.

        Args:
            artist: Artist name
            track: Track name
            limit: Number of similar tracks

        Returns:
            list: Similar tracks with similarity scores
        """
        # Get Last.fm similar tracks
        similar = self.lastfm.get_similar_tracks(artist, track, limit=limit)

        # Enrich with dataset features
        enriched = [self._enrich_with_dataset(t) for t in similar]

        return enriched

    def get_tracks_for_tags(self, tags: List[str], limit: int = 10) -> List[Dict]:
        """
        Get tracks matching specific tags/genres.

        Args:
            tags: List of tag names
            limit: Number of tracks per tag

        Returns:
            list: Tracks matching tags
        """
        all_tracks = []

        for tag in tags[:3]:  # Limit tags
            tracks = self.lastfm.get_tag_top_tracks(tag, limit=limit // len(tags))

            for track in tracks:
                enriched = self._enrich_with_dataset(track)
                enriched["tag"] = tag
                all_tracks.append(enriched)

        return self._deduplicate_and_rank(all_tracks, limit)
