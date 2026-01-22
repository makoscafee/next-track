"""
Model persistence utilities for saving and loading trained models
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

import joblib

logger = logging.getLogger(__name__)

# Default models directory
MODELS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "models"
)


def get_model_path(model_name: str, version: str = None, models_dir: str = None) -> str:
    """
    Get the file path for a model.

    Args:
        model_name: Name of the model
        version: Optional version string (defaults to 'latest')
        models_dir: Directory to store models

    Returns:
        Full path to model file
    """
    models_dir = models_dir or MODELS_DIR
    version = version or "latest"
    return os.path.join(models_dir, f"{model_name}_{version}.joblib")


def save_model(
    model: Any,
    model_name: str,
    version: str = None,
    metadata: Dict = None,
    models_dir: str = None,
) -> str:
    """
    Save a trained model to disk.

    Args:
        model: The trained model object
        model_name: Name for the model
        version: Version string (defaults to timestamp)
        metadata: Optional metadata dict to save alongside model
        models_dir: Directory to save to

    Returns:
        Path to saved model file
    """
    models_dir = models_dir or MODELS_DIR
    os.makedirs(models_dir, exist_ok=True)

    # Generate version if not provided
    if version is None:
        version = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save model
    model_path = get_model_path(model_name, version, models_dir)
    joblib.dump(model, model_path)
    logger.info(f"Saved model to {model_path}")

    # Also save as 'latest'
    latest_path = get_model_path(model_name, "latest", models_dir)
    joblib.dump(model, latest_path)

    # Save metadata
    if metadata is None:
        metadata = {}

    metadata.update(
        {
            "model_name": model_name,
            "version": version,
            "saved_at": datetime.now().isoformat(),
            "model_path": model_path,
        }
    )

    metadata_path = model_path.replace(".joblib", "_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    # Update latest metadata
    latest_metadata_path = latest_path.replace(".joblib", "_metadata.json")
    with open(latest_metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Model version: {version}")

    return model_path


def load_model(
    model_name: str, version: str = "latest", models_dir: str = None
) -> Optional[Any]:
    """
    Load a trained model from disk.

    Args:
        model_name: Name of the model
        version: Version to load (default: 'latest')
        models_dir: Directory to load from

    Returns:
        Loaded model object or None if not found
    """
    models_dir = models_dir or MODELS_DIR
    model_path = get_model_path(model_name, version, models_dir)

    if not os.path.exists(model_path):
        logger.warning(f"Model not found at {model_path}")
        return None

    model = joblib.load(model_path)
    logger.info(f"Loaded model from {model_path}")

    return model


def load_model_metadata(
    model_name: str, version: str = "latest", models_dir: str = None
) -> Optional[Dict]:
    """
    Load model metadata.

    Args:
        model_name: Name of the model
        version: Version to load
        models_dir: Directory to load from

    Returns:
        Metadata dict or None if not found
    """
    models_dir = models_dir or MODELS_DIR
    model_path = get_model_path(model_name, version, models_dir)
    metadata_path = model_path.replace(".joblib", "_metadata.json")

    if not os.path.exists(metadata_path):
        return None

    with open(metadata_path, "r") as f:
        return json.load(f)


def list_model_versions(model_name: str, models_dir: str = None) -> list:
    """
    List all available versions of a model.

    Args:
        model_name: Name of the model
        models_dir: Directory to search

    Returns:
        List of version strings
    """
    models_dir = models_dir or MODELS_DIR

    if not os.path.exists(models_dir):
        return []

    versions = []
    prefix = f"{model_name}_"

    for filename in os.listdir(models_dir):
        if filename.startswith(prefix) and filename.endswith(".joblib"):
            version = filename[len(prefix) : -len(".joblib")]
            if version != "latest":
                versions.append(version)

    return sorted(versions, reverse=True)


def delete_model(model_name: str, version: str, models_dir: str = None) -> bool:
    """
    Delete a model version.

    Args:
        model_name: Name of the model
        version: Version to delete
        models_dir: Directory

    Returns:
        True if deleted successfully
    """
    models_dir = models_dir or MODELS_DIR
    model_path = get_model_path(model_name, version, models_dir)
    metadata_path = model_path.replace(".joblib", "_metadata.json")

    deleted = False

    if os.path.exists(model_path):
        os.remove(model_path)
        deleted = True
        logger.info(f"Deleted {model_path}")

    if os.path.exists(metadata_path):
        os.remove(metadata_path)

    return deleted


class ModelManager:
    """
    High-level model manager for the recommendation system.

    Handles loading and saving all models used by the hybrid recommender.
    """

    MODEL_NAMES = ["content_based", "collaborative", "sentiment_aware", "hybrid"]

    def __init__(self, models_dir: str = None):
        self.models_dir = models_dir or MODELS_DIR
        self.models = {}

    def save_all(
        self, models: Dict[str, Any], version: str = None, metadata: Dict = None
    ):
        """
        Save all models.

        Args:
            models: Dict mapping model names to model objects
            version: Version string (shared across all models)
            metadata: Shared metadata
        """
        if version is None:
            version = datetime.now().strftime("%Y%m%d_%H%M%S")

        for model_name, model in models.items():
            if model is not None:
                save_model(
                    model=model,
                    model_name=model_name,
                    version=version,
                    metadata=metadata,
                    models_dir=self.models_dir,
                )

        logger.info(f"Saved {len(models)} models with version {version}")

    def load_all(self, version: str = "latest") -> Dict[str, Any]:
        """
        Load all models.

        Args:
            version: Version to load

        Returns:
            Dict mapping model names to loaded models
        """
        models = {}

        for model_name in self.MODEL_NAMES:
            model = load_model(model_name, version, self.models_dir)
            if model is not None:
                models[model_name] = model

        logger.info(f"Loaded {len(models)} models")
        return models

    def get_status(self) -> Dict:
        """
        Get status of all models.

        Returns:
            Dict with model status information
        """
        status = {}

        for model_name in self.MODEL_NAMES:
            metadata = load_model_metadata(model_name, "latest", self.models_dir)
            versions = list_model_versions(model_name, self.models_dir)

            status[model_name] = {
                "exists": metadata is not None,
                "latest_version": metadata.get("version") if metadata else None,
                "saved_at": metadata.get("saved_at") if metadata else None,
                "available_versions": versions,
            }

        return status
