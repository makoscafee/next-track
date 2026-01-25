"""
Cached recommenders with Redis support.

Provides caching layer for:
- Content-based recommendation results (by seed features hash)
- Collaborative filtering recommendations (by user ID)
- Track ID lookups
- Model loading on startup
"""

import hashlib
import json
import logging
from typing import Dict, List, Optional

from flask import current_app

from app.ml.collaborative import CollaborativeFilteringRecommender
from app.ml.content_based import ContentBasedRecommender
from app.ml.model_persistence import load_model, load_model_metadata

logger = logging.getLogger(__name__)


def _hash_features(features: Dict) -> str:
    """Create a hash key from feature dict for caching."""
    # Sort keys and round values for consistent hashing
    normalized = {k: round(v, 4) for k, v in sorted(features.items())}
    feature_str = json.dumps(normalized, sort_keys=True)
    return hashlib.md5(feature_str.encode()).hexdigest()[:16]


class CachedContentRecommender:
    """
    Content-based recommender with integrated caching.

    Caches:
    - Recommendations by feature hash (5 min TTL)
    - Recommendations by track ID (5 min TTL)

    Usage:
        recommender = CachedContentRecommender()
        recommender.load_model()  # Load from disk
        recs = recommender.recommend(features, n=10)
    """

    CACHE_PREFIX = "cb_rec:"
    CACHE_TTL = 300  # 5 minutes

    def __init__(self, cache=None):
        """
        Initialize the cached recommender.

        Args:
            cache: Flask-Caching cache instance (optional, uses app cache if None)
        """
        self._cache = cache
        self._model: Optional[ContentBasedRecommender] = None
        self._model_metadata: Optional[Dict] = None
        self._is_loaded = False

    @property
    def cache(self):
        """Get cache instance (lazy loading from app context)."""
        if self._cache is None:
            try:
                from app.extensions import cache

                self._cache = cache
            except ImportError:
                logger.warning(
                    "Cache not available, recommendations will not be cached"
                )
        return self._cache

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded and ready."""
        return self._is_loaded and self._model is not None and self._model.is_fitted

    @property
    def model_info(self) -> Dict:
        """Get information about the loaded model."""
        if not self._is_loaded:
            return {"loaded": False}

        return {
            "loaded": True,
            "n_tracks": len(self._model.track_ids) if self._model else 0,
            "n_neighbors": self._model.n_neighbors if self._model else 0,
            "version": self._model_metadata.get("version")
            if self._model_metadata
            else None,
            "trained_at": self._model_metadata.get("saved_at")
            if self._model_metadata
            else None,
        }

    def load_model(self, version: str = "latest", models_dir: str = None) -> bool:
        """
        Load trained model from disk.

        Args:
            version: Model version to load (default: 'latest')
            models_dir: Optional custom models directory

        Returns:
            bool: True if model loaded successfully
        """
        try:
            model = load_model("content_based", version, models_dir)
            if model is None:
                logger.warning(f"No content_based model found (version: {version})")
                return False

            if not isinstance(model, ContentBasedRecommender):
                logger.error(
                    f"Loaded model is not a ContentBasedRecommender: {type(model)}"
                )
                return False

            self._model = model
            self._model_metadata = load_model_metadata(
                "content_based", version, models_dir
            )
            self._is_loaded = True

            logger.info(
                f"Loaded content_based model (version: {version}, tracks: {len(model.track_ids):,})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def _get_cache_key(self, key_type: str, identifier: str, n: int) -> str:
        """Generate cache key."""
        return f"{self.CACHE_PREFIX}{key_type}:{identifier}:n{n}"

    def _cache_get(self, key: str) -> Optional[List[Dict]]:
        """Get value from cache."""
        if self.cache is None:
            return None
        try:
            return self.cache.get(key)
        except Exception as e:
            logger.debug(f"Cache get error: {e}")
            return None

    def _cache_set(self, key: str, value: List[Dict]) -> None:
        """Set value in cache."""
        if self.cache is None:
            return
        try:
            self.cache.set(key, value, timeout=self.CACHE_TTL)
        except Exception as e:
            logger.debug(f"Cache set error: {e}")

    def recommend(
        self,
        seed_features: Dict,
        n_recommendations: int = 10,
        use_cache: bool = True,
    ) -> List[Dict]:
        """
        Get recommendations based on audio features.

        Args:
            seed_features: Dict of audio feature values
            n_recommendations: Number of recommendations
            use_cache: Whether to use caching (default: True)

        Returns:
            List of recommendations with track_id and similarity_score
        """
        if not self.is_loaded:
            logger.warning("Model not loaded, returning empty recommendations")
            return []

        # Check cache
        if use_cache:
            feature_hash = _hash_features(seed_features)
            cache_key = self._get_cache_key("feat", feature_hash, n_recommendations)
            cached = self._cache_get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for features: {cache_key}")
                return cached

        # Get recommendations from model
        recommendations = self._model.recommend(seed_features, n_recommendations)

        # Cache results
        if use_cache:
            self._cache_set(cache_key, recommendations)

        return recommendations

    def recommend_from_track_id(
        self,
        track_id: str,
        n_recommendations: int = 10,
        use_cache: bool = True,
    ) -> List[Dict]:
        """
        Get recommendations similar to a specific track.

        Args:
            track_id: ID of the seed track
            n_recommendations: Number of recommendations
            use_cache: Whether to use caching (default: True)

        Returns:
            List of recommendations with track_id and similarity_score
        """
        if not self.is_loaded:
            logger.warning("Model not loaded, returning empty recommendations")
            return []

        # Check cache
        if use_cache:
            cache_key = self._get_cache_key("track", track_id, n_recommendations)
            cached = self._cache_get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for track: {cache_key}")
                return cached

        # Get recommendations from model
        recommendations = self._model.recommend_from_track_id(
            track_id, n_recommendations
        )

        # Cache results
        if use_cache:
            self._cache_set(cache_key, recommendations)

        return recommendations

    def clear_cache(self) -> None:
        """Clear all recommendation cache entries."""
        if self.cache is None:
            return

        try:
            # Note: This is a simple implementation
            # For production, you might want to use cache.delete_many with pattern matching
            self.cache.clear()
            logger.info("Recommendation cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")

    def get_track_ids(self) -> List[str]:
        """Get all track IDs in the model."""
        if not self.is_loaded:
            return []
        return list(self._model.track_ids)

    def has_track(self, track_id: str) -> bool:
        """Check if a track ID exists in the model."""
        if not self.is_loaded:
            return False
        return track_id in self._model.track_ids


class CachedCollaborativeRecommender:
    """
    Collaborative filtering recommender with integrated caching.

    Caches:
    - Recommendations by user ID (5 min TTL)
    - Similar users (5 min TTL)
    """

    CACHE_PREFIX = "cf_rec:"
    CACHE_TTL = 300  # 5 minutes

    def __init__(self, cache=None):
        """Initialize the cached CF recommender."""
        self._cache = cache
        self._model: Optional[CollaborativeFilteringRecommender] = None
        self._model_metadata: Optional[Dict] = None
        self._is_loaded = False

    @property
    def cache(self):
        """Get cache instance."""
        if self._cache is None:
            try:
                from app.extensions import cache

                self._cache = cache
            except ImportError:
                pass
        return self._cache

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded and ready."""
        return self._is_loaded and self._model is not None and self._model.is_fitted

    @property
    def model_info(self) -> Dict:
        """Get information about the loaded model."""
        if not self._is_loaded:
            return {"loaded": False}

        return {
            "loaded": True,
            "n_users": len(self._model.user_mapping) if self._model.user_mapping else 0,
            "n_tracks": len(self._model.track_mapping)
            if self._model.track_mapping
            else 0,
            "n_factors": self._model.n_factors if self._model else 0,
            "version": self._model_metadata.get("version")
            if self._model_metadata
            else None,
            "trained_at": self._model_metadata.get("saved_at")
            if self._model_metadata
            else None,
        }

    def load_model(self, version: str = "latest", models_dir: str = None) -> bool:
        """Load trained model from disk."""
        try:
            model = load_model("collaborative", version, models_dir)
            if model is None:
                logger.warning(f"No collaborative model found (version: {version})")
                return False

            if not isinstance(model, CollaborativeFilteringRecommender):
                logger.error(
                    f"Loaded model is not a CollaborativeFilteringRecommender: {type(model)}"
                )
                return False

            self._model = model
            self._model_metadata = load_model_metadata(
                "collaborative", version, models_dir
            )
            self._is_loaded = True

            logger.info(
                f"Loaded collaborative model (version: {version}, users: {len(model.user_mapping):,})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to load CF model: {e}")
            return False

    def _get_cache_key(self, key_type: str, identifier: str, n: int) -> str:
        """Generate cache key."""
        return f"{self.CACHE_PREFIX}{key_type}:{identifier}:n{n}"

    def _cache_get(self, key: str) -> Optional[List[Dict]]:
        """Get value from cache."""
        if self.cache is None:
            return None
        try:
            return self.cache.get(key)
        except Exception:
            return None

    def _cache_set(self, key: str, value: List[Dict]) -> None:
        """Set value in cache."""
        if self.cache is None:
            return
        try:
            self.cache.set(key, value, timeout=self.CACHE_TTL)
        except Exception:
            pass

    def recommend_for_user(
        self,
        user_id: str,
        n_recommendations: int = 10,
        use_cache: bool = True,
    ) -> List[Dict]:
        """
        Get recommendations for a user.

        Args:
            user_id: User identifier
            n_recommendations: Number of recommendations
            use_cache: Whether to use caching

        Returns:
            List of recommendations with track_id and cf_score
        """
        if not self.is_loaded:
            logger.warning("CF model not loaded, returning empty recommendations")
            return []

        # Check cache
        if use_cache:
            cache_key = self._get_cache_key("user", user_id, n_recommendations)
            cached = self._cache_get(cache_key)
            if cached is not None:
                return cached

        # Get recommendations
        recommendations = self._model.recommend_for_user(user_id, n_recommendations)

        # Cache results
        if use_cache and recommendations:
            self._cache_set(cache_key, recommendations)

        return recommendations

    def get_similar_users(
        self,
        user_id: str,
        n_users: int = 10,
        use_cache: bool = True,
    ) -> List[Dict]:
        """
        Find users similar to a given user.

        Args:
            user_id: User identifier
            n_users: Number of similar users
            use_cache: Whether to use caching

        Returns:
            List of similar users with similarity scores
        """
        if not self.is_loaded:
            return []

        # Check cache
        if use_cache:
            cache_key = self._get_cache_key("similar", user_id, n_users)
            cached = self._cache_get(cache_key)
            if cached is not None:
                return cached

        # Get similar users
        similar = self._model.get_similar_users(user_id, n_users)

        # Cache results
        if use_cache and similar:
            self._cache_set(cache_key, similar)

        return similar

    def has_user(self, user_id: str) -> bool:
        """Check if user exists in the model."""
        if not self.is_loaded or not self._model.user_mapping:
            return False
        return user_id in self._model.user_mapping


# Singleton instances for app-wide use
_cached_content_recommender: Optional[CachedContentRecommender] = None
_cached_cf_recommender: Optional[CachedCollaborativeRecommender] = None


def get_cached_recommender() -> CachedContentRecommender:
    """Get or create the singleton cached content recommender instance."""
    global _cached_content_recommender
    if _cached_content_recommender is None:
        _cached_content_recommender = CachedContentRecommender()
    return _cached_content_recommender


def get_cached_cf_recommender() -> CachedCollaborativeRecommender:
    """Get or create the singleton cached CF recommender instance."""
    global _cached_cf_recommender
    if _cached_cf_recommender is None:
        _cached_cf_recommender = CachedCollaborativeRecommender()
    return _cached_cf_recommender


def init_cached_recommender(app=None) -> CachedContentRecommender:
    """
    Initialize the cached content recommender and load the model.

    Call this during app startup to ensure model is loaded.

    Args:
        app: Flask app instance (optional)

    Returns:
        CachedContentRecommender instance
    """
    recommender = get_cached_recommender()

    if not recommender.is_loaded:
        success = recommender.load_model()
        if success:
            logger.info(
                f"Content-based recommender initialized: {recommender.model_info}"
            )
        else:
            logger.warning(
                "Content-based model not available - train with scripts/train_content_model.py"
            )

    return recommender


def init_cached_cf_recommender(app=None) -> CachedCollaborativeRecommender:
    """
    Initialize the cached CF recommender and load the model.

    Args:
        app: Flask app instance (optional)

    Returns:
        CachedCollaborativeRecommender instance
    """
    recommender = get_cached_cf_recommender()

    if not recommender.is_loaded:
        success = recommender.load_model()
        if success:
            logger.info(
                f"Collaborative recommender initialized: {recommender.model_info}"
            )
        else:
            logger.warning(
                "Collaborative model not available - train with scripts/train_collaborative_model.py"
            )

    return recommender


def init_all_recommenders(app=None) -> Dict:
    """
    Initialize all recommender models.

    Args:
        app: Flask app instance

    Returns:
        Dict with model info for each recommender
    """
    content = init_cached_recommender(app)
    cf = init_cached_cf_recommender(app)

    return {
        "content_based": content.model_info,
        "collaborative": cf.model_info,
    }
