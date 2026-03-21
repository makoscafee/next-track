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
        List all A/B test experiments.
        ---
        tags:
          - Experiments
        responses:
          200:
            description: All experiments
            schema:
              type: object
              properties:
                experiments:
                  type: array
                  items:
                    type: object
                count:
                  type: integer
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
        Get details and current results for an experiment.
        ---
        tags:
          - Experiments
        parameters:
          - in: path
            name: experiment_name
            type: string
            required: true
            example: hybrid_weights
        responses:
          200:
            description: Experiment results by variant
            schema:
              type: object
          404:
            description: Experiment not found
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
        Get the variant assigned to a specific user.
        ---
        tags:
          - Experiments
        parameters:
          - in: path
            name: experiment_name
            type: string
            required: true
            example: hybrid_weights
          - in: query
            name: user_id
            type: string
            required: true
            example: user_123
        responses:
          200:
            description: User's variant assignment
            schema:
              type: object
              properties:
                experiment:
                  type: string
                user_id:
                  type: string
                variant:
                  type: object
                  properties:
                    name:
                      type: string
                    config:
                      type: object
          400:
            description: Missing user_id
          404:
            description: Experiment not found or not running
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
        Record a metric observation for an experiment variant.
        ---
        tags:
          - Experiments
        parameters:
          - in: path
            name: experiment_name
            type: string
            required: true
            example: hybrid_weights
          - in: body
            name: body
            required: true
            schema:
              type: object
              required: [user_id, metric_name, value]
              properties:
                user_id:
                  type: string
                  example: user_123
                metric_name:
                  type: string
                  example: play_rate
                value:
                  type: number
                  example: 1.0
        responses:
          201:
            description: Metric recorded
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: recorded
                experiment:
                  type: string
                metric:
                  type: string
                value:
                  type: number
          400:
            description: Missing required fields
          404:
            description: Experiment not found
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
        Record user feedback for a recommended track.
        ---
        tags:
          - Experiments
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required: [user_id, track_id, feedback_type]
              properties:
                user_id:
                  type: string
                  example: user_123
                track_id:
                  type: string
                  example: 4u7EnebtmKWzUH433cf5Qv
                feedback_type:
                  type: string
                  enum: [click, play, skip, save, listen_time]
                  example: play
                value:
                  type: number
                  default: 1.0
                  example: 1.0
        responses:
          201:
            description: Feedback recorded
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: recorded
                feedback_type:
                  type: string
                value:
                  type: number
          400:
            description: Missing required fields or invalid feedback_type
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
