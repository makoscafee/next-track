"""
A/B Testing Framework for recommendation strategies.

Supports multiple experiment variants with configurable traffic allocation,
metric tracking, and statistical significance testing.
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np


class ExperimentStatus(Enum):
    """Status of an A/B test experiment."""

    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


@dataclass
class Variant:
    """A single variant in an A/B test."""

    name: str
    weight: float  # Traffic allocation (0-1)
    config: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, List[float]] = field(default_factory=dict)

    def add_metric(self, metric_name: str, value: float):
        """Record a metric observation for this variant."""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(value)

    def get_metric_stats(self, metric_name: str) -> Dict[str, float]:
        """Get statistics for a metric."""
        values = self.metrics.get(metric_name, [])
        if not values:
            return {"count": 0, "mean": 0, "std": 0, "min": 0, "max": 0}

        return {
            "count": len(values),
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
        }


@dataclass
class Experiment:
    """An A/B test experiment with multiple variants."""

    name: str
    description: str
    variants: List[Variant]
    status: ExperimentStatus = ExperimentStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate and normalize variant weights."""
        total_weight = sum(v.weight for v in self.variants)
        if total_weight > 0:
            for v in self.variants:
                v.weight = v.weight / total_weight

    def get_variant_for_user(self, user_id: str) -> Variant:
        """
        Deterministically assign a user to a variant based on their ID.

        Uses consistent hashing so users always get the same variant.
        """
        hash_input = f"{self.name}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        bucket = (hash_value % 1000) / 1000.0

        cumulative = 0.0
        for variant in self.variants:
            cumulative += variant.weight
            if bucket < cumulative:
                return variant

        return self.variants[-1]  # Fallback to last variant

    def start(self):
        """Start the experiment."""
        self.status = ExperimentStatus.RUNNING
        self.started_at = datetime.now()

    def pause(self):
        """Pause the experiment."""
        self.status = ExperimentStatus.PAUSED

    def complete(self):
        """Mark experiment as completed."""
        self.status = ExperimentStatus.COMPLETED
        self.ended_at = datetime.now()

    def get_results(self) -> Dict[str, Any]:
        """Get experiment results with statistical analysis."""
        results = {
            "experiment": self.name,
            "status": self.status.value,
            "duration_hours": None,
            "variants": {},
        }

        if self.started_at:
            end = self.ended_at or datetime.now()
            results["duration_hours"] = (end - self.started_at).total_seconds() / 3600

        for variant in self.variants:
            results["variants"][variant.name] = {
                "weight": variant.weight,
                "config": variant.config,
                "metrics": {
                    name: variant.get_metric_stats(name)
                    for name in variant.metrics.keys()
                },
            }

        return results


class ABTestManager:
    """
    Manages multiple A/B test experiments.

    Provides experiment creation, user assignment, metric tracking,
    and result analysis.
    """

    def __init__(self):
        """Initialize the A/B test manager."""
        self.experiments: Dict[str, Experiment] = {}
        self._default_experiment: Optional[str] = None

    def create_experiment(
        self,
        name: str,
        description: str,
        variants: List[Dict[str, Any]],
        auto_start: bool = False,
    ) -> Experiment:
        """
        Create a new A/B test experiment.

        Args:
            name: Unique experiment name
            description: Human-readable description
            variants: List of variant configs with 'name', 'weight', and optional 'config'
            auto_start: Whether to start the experiment immediately

        Returns:
            The created Experiment
        """
        variant_objects = [
            Variant(
                name=v["name"],
                weight=v.get("weight", 1.0),
                config=v.get("config", {}),
            )
            for v in variants
        ]

        experiment = Experiment(
            name=name,
            description=description,
            variants=variant_objects,
        )

        if auto_start:
            experiment.start()

        self.experiments[name] = experiment
        return experiment

    def get_experiment(self, name: str) -> Optional[Experiment]:
        """Get an experiment by name."""
        return self.experiments.get(name)

    def get_variant(self, experiment_name: str, user_id: str) -> Optional[Variant]:
        """
        Get the variant assigned to a user for an experiment.

        Args:
            experiment_name: Name of the experiment
            user_id: User identifier

        Returns:
            The assigned Variant or None if experiment not found
        """
        experiment = self.experiments.get(experiment_name)
        if not experiment or experiment.status != ExperimentStatus.RUNNING:
            return None

        return experiment.get_variant_for_user(user_id)

    def record_metric(
        self,
        experiment_name: str,
        user_id: str,
        metric_name: str,
        value: float,
    ):
        """
        Record a metric for a user's assigned variant.

        Args:
            experiment_name: Name of the experiment
            user_id: User identifier
            metric_name: Name of the metric (e.g., 'click_rate', 'listen_time')
            value: Metric value
        """
        variant = self.get_variant(experiment_name, user_id)
        if variant:
            variant.add_metric(metric_name, value)

    def get_results(self, experiment_name: str) -> Optional[Dict[str, Any]]:
        """Get results for an experiment."""
        experiment = self.experiments.get(experiment_name)
        if not experiment:
            return None
        return experiment.get_results()

    def set_default_experiment(self, name: str):
        """Set the default experiment for recommendations."""
        if name in self.experiments:
            self._default_experiment = name

    def get_default_experiment(self) -> Optional[Experiment]:
        """Get the default experiment."""
        if self._default_experiment:
            return self.experiments.get(self._default_experiment)
        return None

    def list_experiments(self) -> List[Dict[str, Any]]:
        """List all experiments with basic info."""
        return [
            {
                "name": exp.name,
                "description": exp.description,
                "status": exp.status.value,
                "variants": [v.name for v in exp.variants],
                "created_at": exp.created_at.isoformat(),
            }
            for exp in self.experiments.values()
        ]


# Pre-configured recommendation experiments
def create_default_experiments(manager: ABTestManager):
    """Create default recommendation experiments."""

    # Experiment 1: Model weight tuning
    manager.create_experiment(
        name="hybrid_weights",
        description="Compare different hybrid model weight configurations",
        variants=[
            {
                "name": "control",
                "weight": 0.5,
                "config": {
                    "content_weight": 0.4,
                    "collab_weight": 0.35,
                    "sentiment_weight": 0.25,
                },
            },
            {
                "name": "content_heavy",
                "weight": 0.25,
                "config": {
                    "content_weight": 0.6,
                    "collab_weight": 0.25,
                    "sentiment_weight": 0.15,
                },
            },
            {
                "name": "sentiment_heavy",
                "weight": 0.25,
                "config": {
                    "content_weight": 0.3,
                    "collab_weight": 0.3,
                    "sentiment_weight": 0.4,
                },
            },
        ],
        auto_start=True,
    )

    # Experiment 2: Diversity levels
    manager.create_experiment(
        name="diversity_level",
        description="Compare recommendation diversity settings",
        variants=[
            {
                "name": "low_diversity",
                "weight": 0.33,
                "config": {"diversity_factor": 0.1},
            },
            {
                "name": "medium_diversity",
                "weight": 0.34,
                "config": {"diversity_factor": 0.3},
            },
            {
                "name": "high_diversity",
                "weight": 0.33,
                "config": {"diversity_factor": 0.5},
            },
        ],
        auto_start=True,
    )

    # Experiment 3: Serendipity injection
    manager.create_experiment(
        name="serendipity",
        description="Test serendipity (surprise) injection in recommendations",
        variants=[
            {
                "name": "no_serendipity",
                "weight": 0.5,
                "config": {"serendipity_factor": 0.0},
            },
            {
                "name": "with_serendipity",
                "weight": 0.5,
                "config": {"serendipity_factor": 0.15},
            },
        ],
        auto_start=True,
    )

    return manager


# Singleton instance
_ab_manager: Optional[ABTestManager] = None


def get_ab_manager() -> ABTestManager:
    """Get the singleton A/B test manager instance."""
    global _ab_manager
    if _ab_manager is None:
        _ab_manager = ABTestManager()
        create_default_experiments(_ab_manager)
    return _ab_manager
