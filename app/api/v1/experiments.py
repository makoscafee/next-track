"""
A/B Testing API endpoints for experiments management.
"""

from flask import request
from flask_restful import Resource

from app.ml.ab_testing import get_ab_manager


class ExperimentsListResource(Resource):
    """List and manage A/B test experiments."""

    def get(self):
        """
        List all experiments.

        Returns:
            200: List of experiments with basic info
        """
        ab_manager = get_ab_manager()
        experiments = ab_manager.list_experiments()

        return {
            "experiments": experiments,
            "count": len(experiments),
        }, 200


class ExperimentResource(Resource):
    """Get details and results for a specific experiment."""

    def get(self, experiment_name):
        """
        Get experiment details and results.

        Args:
            experiment_name: Name of the experiment

        Returns:
            200: Experiment details with variant results
            404: Experiment not found
        """
        ab_manager = get_ab_manager()
        results = ab_manager.get_results(experiment_name)

        if results is None:
            return {"error": f"Experiment '{experiment_name}' not found"}, 404

        return results, 200


class ExperimentVariantResource(Resource):
    """Get variant assignment for a user."""

    def get(self, experiment_name):
        """
        Get the variant assigned to a user for an experiment.

        Args:
            experiment_name: Name of the experiment

        Query params:
            user_id (required): User identifier

        Returns:
            200: Variant assignment details
            400: Missing user_id
            404: Experiment not found or not running
        """
        user_id = request.args.get("user_id")

        if not user_id:
            return {"error": "user_id query parameter is required"}, 400

        ab_manager = get_ab_manager()
        variant = ab_manager.get_variant(experiment_name, user_id)

        if variant is None:
            return {
                "error": f"Experiment '{experiment_name}' not found or not running"
            }, 404

        return {
            "experiment": experiment_name,
            "user_id": user_id,
            "variant": {
                "name": variant.name,
                "config": variant.config,
            },
        }, 200


class ExperimentMetricResource(Resource):
    """Record metrics for A/B testing."""

    def post(self, experiment_name):
        """
        Record a metric observation for an experiment.

        Args:
            experiment_name: Name of the experiment

        Body (JSON):
            user_id (required): User identifier
            metric_name (required): Name of the metric
            value (required): Metric value (number)

        Returns:
            201: Metric recorded
            400: Missing required fields
            404: Experiment not found
        """
        data = request.get_json() or {}

        user_id = data.get("user_id")
        metric_name = data.get("metric_name")
        value = data.get("value")

        if not user_id:
            return {"error": "user_id is required"}, 400
        if not metric_name:
            return {"error": "metric_name is required"}, 400
        if value is None:
            return {"error": "value is required"}, 400

        try:
            value = float(value)
        except (TypeError, ValueError):
            return {"error": "value must be a number"}, 400

        ab_manager = get_ab_manager()
        experiment = ab_manager.get_experiment(experiment_name)

        if experiment is None:
            return {"error": f"Experiment '{experiment_name}' not found"}, 404

        ab_manager.record_metric(experiment_name, user_id, metric_name, value)

        return {
            "status": "recorded",
            "experiment": experiment_name,
            "user_id": user_id,
            "metric": metric_name,
            "value": value,
        }, 201


class FeedbackResource(Resource):
    """Record user feedback for recommendations."""

    def post(self):
        """
        Record user feedback for a recommendation.

        Body (JSON):
            user_id (required): User identifier
            track_id (required): Track that received feedback
            feedback_type (required): Type of feedback (click, play, skip, save, listen_time)
            value (optional): Feedback value (default 1.0)

        Returns:
            201: Feedback recorded
            400: Missing required fields
        """
        data = request.get_json() or {}

        user_id = data.get("user_id")
        track_id = data.get("track_id")
        feedback_type = data.get("feedback_type")
        value = data.get("value", 1.0)

        if not user_id:
            return {"error": "user_id is required"}, 400
        if not track_id:
            return {"error": "track_id is required"}, 400
        if not feedback_type:
            return {"error": "feedback_type is required"}, 400

        valid_types = ["click", "play", "skip", "save", "listen_time"]
        if feedback_type not in valid_types:
            return {
                "error": f"feedback_type must be one of: {', '.join(valid_types)}"
            }, 400

        try:
            value = float(value)
        except (TypeError, ValueError):
            return {"error": "value must be a number"}, 400

        # Record feedback to all relevant experiments
        ab_manager = get_ab_manager()
        metric_map = {
            "click": "click_rate",
            "play": "play_rate",
            "skip": "skip_rate",
            "save": "save_rate",
            "listen_time": "avg_listen_time",
        }
        metric_name = metric_map.get(feedback_type, feedback_type)

        for exp_name in ["hybrid_weights", "diversity_level", "serendipity"]:
            if ab_manager.get_experiment(exp_name):
                ab_manager.record_metric(exp_name, user_id, metric_name, value)

        # Record to admin feedback log
        from app.api.v1.admin import record_feedback_log

        record_feedback_log(user_id, track_id, feedback_type, value)

        return {
            "status": "recorded",
            "user_id": user_id,
            "track_id": track_id,
            "feedback_type": feedback_type,
            "value": value,
        }, 201
