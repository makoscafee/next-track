"""
Recommendation service - orchestrates the hybrid recommendation system
Combines Last.fm similarity data with Kaggle dataset audio features
with A/B testing, explanations, and diversity controls.
"""

from typing import Any, Dict, List, Optional

from app.ml.hybrid import HybridRecommender
from app.services.dataset_service import DatasetService
from app.services.lastfm_service import LastFMService


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
        context: Optional[Dict] = None,
        include_explanation: bool = False,
        diversity_factor: Optional[float] = None,
        serendipity_factor: Optional[float] = None,
    ) -> List[Dict]:
        """
        Get hybrid recommendations combining Last.fm and dataset.

        Args:
            user_id: Optional user ID for personalized recommendations and A/B testing
            seed_tracks: List of seed tracks [{'name': str, 'artist': str}, ...]
            mood: Optional mood string (e.g., 'happy', 'sad', 'energetic')
            limit: Number of recommendations
            context: Optional context dict with time_of_day, activity, weather
            include_explanation: Whether to include detailed explanations
            diversity_factor: Override diversity factor (0-1)
            serendipity_factor: Override serendipity factor (0-1)

        Returns:
            list: Recommended tracks with scores and metadata
        """
        recommendations = []

        # Strategy 1: Use Last.fm similar tracks if seed tracks provided
        if seed_tracks:
            lastfm_recs = self._get_lastfm_recommendations(seed_tracks, limit * 2)
            recommendations.extend(lastfm_recs)

        # Strategy 2: Use mood-based recommendations from dataset (context-aware)
        if mood:
            mood_recs = self._get_mood_recommendations(mood, limit, context)
            recommendations.extend(mood_recs)

        # Strategy 3: If we have dataset features, use hybrid model with A/B testing
        if self._models_initialized:
            seed_features = None

            # Extract seed features if seed tracks provided
            if seed_tracks:
                seed_features = self._get_seed_features(seed_tracks)

            # Use hybrid model (includes A/B testing, diversity, serendipity)
            if seed_features or mood or user_id:
                hybrid_recs = self.hybrid_model.recommend(
                    user_id=user_id,
                    seed_track_features=seed_features,
                    mood=mood,
                    n_recommendations=limit,
                    include_explanation=include_explanation,
                    context=context,
                    diversity_factor=diversity_factor,
                    serendipity_factor=serendipity_factor,
                )

                # Enrich hybrid recommendations with track metadata
                for rec in hybrid_recs:
                    track = self.dataset.get_track_by_id(rec["track_id"])
                    if track:
                        enriched = {
                            "name": track.get("name"),
                            "artist": track.get("artists"),
                            "track_id": rec["track_id"],
                            "score": rec["score"],
                            "source": "hybrid",
                            "explanation": rec.get("explanation", ""),
                            "audio_features": self.dataset.get_audio_features(
                                rec["track_id"]
                            ),
                        }

                        # Include detailed explanation if available
                        if "detailed_explanation" in rec:
                            enriched["detailed_explanation"] = rec[
                                "detailed_explanation"
                            ]

                        recommendations.append(enriched)

        # Deduplicate and rank
        recommendations = self._deduplicate_and_rank(recommendations, limit)

        # Fallback to chart tracks if no recommendations
        if not recommendations:
            recommendations = self._get_fallback_recommendations(limit)

        return recommendations

    def _get_seed_features(self, seed_tracks: List[Dict]) -> Optional[Dict[str, float]]:
        """Extract audio features from seed tracks."""
        for seed in seed_tracks[:2]:
            track_data = self.dataset.get_track_by_name(
                seed.get("name", ""), seed.get("artist")
            )

            if track_data:
                return {
                    "danceability": track_data.get("danceability", 0.5),
                    "energy": track_data.get("energy", 0.5),
                    "valence": track_data.get("valence", 0.5),
                    "tempo": track_data.get("tempo", 120),
                    "acousticness": track_data.get("acousticness", 0.5),
                    "instrumentalness": track_data.get("instrumentalness", 0.5),
                    "speechiness": track_data.get("speechiness", 0.5),
                }

        return None

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

    def _get_mood_recommendations(
        self, mood: str, limit: int, context: Optional[Dict] = None
    ) -> List[Dict]:
        """Get context-aware mood-based recommendations from dataset."""
        # Research-backed mood to valence/energy mapping (wider ranges for filtering)
        mood_mapping = {
            # High valence, high arousal
            "happy": {"valence": (0.60, 1.0), "energy": (0.50, 1.0)},
            "joy": {"valence": (0.65, 1.0), "energy": (0.55, 1.0)},
            "excited": {"valence": (0.55, 1.0), "energy": (0.70, 1.0)},
            "energetic": {"valence": (0.45, 1.0), "energy": (0.70, 1.0)},
            # High valence, low arousal
            "calm": {"valence": (0.45, 0.80), "energy": (0.0, 0.45)},
            "relaxed": {"valence": (0.50, 0.85), "energy": (0.0, 0.40)},
            "peaceful": {"valence": (0.42, 0.78), "energy": (0.0, 0.35)},
            # Low valence, low arousal
            "sad": {"valence": (0.0, 0.35), "energy": (0.0, 0.45)},
            "melancholic": {"valence": (0.10, 0.45), "energy": (0.15, 0.50)},
            # Low valence, high arousal
            "angry": {"valence": (0.0, 0.35), "energy": (0.70, 1.0)},
            "anxious": {"valence": (0.10, 0.50), "energy": (0.55, 0.90)},
            "fear": {"valence": (0.05, 0.40), "energy": (0.65, 1.0)},
            # Neutral/mixed
            "neutral": {"valence": (0.30, 0.70), "energy": (0.30, 0.65)},
            "surprise": {"valence": (0.35, 0.75), "energy": (0.60, 0.95)},
        }

        params = mood_mapping.get(
            mood.lower(), {"valence": (0.30, 0.70), "energy": (0.30, 0.70)}
        )

        # Apply context modifiers to the target ranges
        valence_range = list(params["valence"])
        energy_range = list(params["energy"])

        if context:
            # Context modifiers shift the ranges
            context_mods = self._get_context_modifiers(context)
            v_mod, e_mod = context_mods

            # Shift ranges while keeping them within bounds
            valence_range[0] = max(0.0, min(1.0, valence_range[0] + v_mod))
            valence_range[1] = max(0.0, min(1.0, valence_range[1] + v_mod))
            energy_range[0] = max(0.0, min(1.0, energy_range[0] + e_mod))
            energy_range[1] = max(0.0, min(1.0, energy_range[1] + e_mod))

        tracks = self.dataset.get_tracks_by_mood(
            tuple(valence_range), tuple(energy_range), limit=limit
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
                "context_applied": context is not None,
            }
            for t in tracks
        ]

    def _get_context_modifiers(self, context: Dict) -> tuple:
        """Get valence/energy modifiers based on context."""
        time_mods = {
            "morning": (0.05, 0.10),
            "afternoon": (0.0, 0.0),
            "evening": (0.0, -0.08),
            "night": (-0.02, -0.15),
        }
        activity_mods = {
            "workout": (0.08, 0.20),
            "work": (-0.02, 0.05),
            "relaxation": (0.05, -0.20),
            "party": (0.10, 0.25),
            "commute": (0.0, 0.0),
            "focus": (0.0, 0.10),
            "social": (0.08, 0.10),
        }
        weather_mods = {
            "sunny": (0.08, 0.05),
            "rainy": (-0.05, -0.08),
            "cloudy": (-0.03, -0.03),
            "cold": (-0.02, -0.05),
            "hot": (0.02, 0.05),
        }

        v_mod, e_mod = 0.0, 0.0

        if context.get("time_of_day"):
            mods = time_mods.get(context["time_of_day"], (0, 0))
            v_mod += mods[0]
            e_mod += mods[1]

        if context.get("activity"):
            mods = activity_mods.get(context["activity"], (0, 0))
            v_mod += mods[0]
            e_mod += mods[1]

        if context.get("weather"):
            mods = weather_mods.get(context["weather"], (0, 0))
            v_mod += mods[0]
            e_mod += mods[1]

        return (v_mod, e_mod)

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

    def record_feedback(
        self,
        user_id: str,
        track_id: str,
        feedback_type: str,
        value: float = 1.0,
    ):
        """
        Record user feedback for A/B testing.

        Args:
            user_id: User identifier
            track_id: Track that received feedback
            feedback_type: Type of feedback (click, play, skip, save)
            value: Feedback value
        """
        self.hybrid_model.record_feedback(user_id, track_id, feedback_type, value)

    def get_ab_results(self, experiment_name: str) -> Optional[Dict[str, Any]]:
        """Get A/B test results for an experiment."""
        return self.hybrid_model.get_ab_results(experiment_name)

    def list_experiments(self) -> List[Dict[str, Any]]:
        """List all A/B test experiments."""
        return self.hybrid_model.list_experiments()
