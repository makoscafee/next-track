"""
Admin API endpoints for dashboard.
"""

from datetime import datetime
from typing import Any, Dict, List

from flask import request
from flask_restful import Resource

from app.api.v1.auth import admin_required
from app.ml.ab_testing import get_ab_manager
from app.ml.cached_recommender import get_cached_cf_recommender, get_cached_recommender

# In-memory feedback storage (in production, use database)
_feedback_log: List[Dict[str, Any]] = []
MAX_FEEDBACK_LOG = 1000


def record_feedback_log(
    user_id: str,
    track_id: str,
    feedback_type: str,
    value: float,
):
    """Record feedback to the log for admin viewing."""
    global _feedback_log

    _feedback_log.append(
        {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "track_id": track_id,
            "feedback_type": feedback_type,
            "value": value,
        }
    )

    # Keep only the most recent entries
    if len(_feedback_log) > MAX_FEEDBACK_LOG:
        _feedback_log = _feedback_log[-MAX_FEEDBACK_LOG:]


class AdminStatsResource(Resource):
    """Get aggregated system statistics."""

    @admin_required
    def get(self):
        """
        Get aggregated system statistics (models, experiments, feedback).
        ---
        tags:
          - Admin
        security:
          - Bearer: []
        responses:
          200:
            description: System statistics
            schema:
              type: object
              properties:
                models:
                  type: object
                experiments:
                  type: array
                  items:
                    type: object
                feedback:
                  type: object
                  properties:
                    total:
                      type: integer
                    by_type:
                      type: object
                generated_at:
                  type: string
          401:
            description: Unauthorised
          403:
            description: Admin access required
        """
        # Get model info
        content_rec = get_cached_recommender()
        cf_rec = get_cached_cf_recommender()

        # Get experiment stats
        ab_manager = get_ab_manager()
        experiments = ab_manager.list_experiments()

        # Aggregate experiment metrics
        experiment_stats = []
        for exp_info in experiments:
            exp_name = exp_info["name"]
            results = ab_manager.get_results(exp_name)
            if results:
                total_observations = 0
                for variant_name, variant_data in results.get("variants", {}).items():
                    for metric_name, metric_stats in variant_data.get(
                        "metrics", {}
                    ).items():
                        total_observations += metric_stats.get("count", 0)

                experiment_stats.append(
                    {
                        "name": exp_name,
                        "status": exp_info["status"],
                        "variants": len(results.get("variants", {})),
                        "total_observations": total_observations,
                    }
                )

        # Feedback stats
        feedback_counts = {}
        for fb in _feedback_log:
            fb_type = fb["feedback_type"]
            feedback_counts[fb_type] = feedback_counts.get(fb_type, 0) + 1

        return {
            "models": {
                "content_based": content_rec.model_info,
                "collaborative": cf_rec.model_info,
            },
            "experiments": experiment_stats,
            "feedback": {
                "total": len(_feedback_log),
                "by_type": feedback_counts,
            },
            "generated_at": datetime.now().isoformat(),
        }, 200


class AdminFeedbackLogResource(Resource):
    """Get recent feedback log entries."""

    @admin_required
    def get(self):
        """
        Get recent feedback log entries.
        ---
        tags:
          - Admin
        security:
          - Bearer: []
        parameters:
          - in: query
            name: limit
            type: integer
            default: 50
            maximum: 200
          - in: query
            name: feedback_type
            type: string
            enum: [click, play, skip, save, listen_time]
            description: Filter by feedback type
        responses:
          200:
            description: Feedback log entries
            schema:
              type: object
              properties:
                entries:
                  type: array
                  items:
                    type: object
                    properties:
                      timestamp:
                        type: string
                      user_id:
                        type: string
                      track_id:
                        type: string
                      feedback_type:
                        type: string
                      value:
                        type: number
                count:
                  type: integer
                total_in_log:
                  type: integer
          401:
            description: Unauthorised
          403:
            description: Admin access required
        """
        limit = min(int(request.args.get("limit", 50)), 200)
        feedback_type = request.args.get("feedback_type")

        entries = _feedback_log.copy()

        # Filter by type if specified
        if feedback_type:
            entries = [e for e in entries if e["feedback_type"] == feedback_type]

        # Return most recent first
        entries = list(reversed(entries))[:limit]

        return {
            "entries": entries,
            "count": len(entries),
            "total_in_log": len(_feedback_log),
        }, 200


class AdminExperimentDetailResource(Resource):
    """Get detailed experiment results for admin."""

    @admin_required
    def get(self, experiment_name):
        """
        Get detailed experiment results with cross-variant metric comparison.
        ---
        tags:
          - Admin
        security:
          - Bearer: []
        parameters:
          - in: path
            name: experiment_name
            type: string
            required: true
            example: hybrid_weights
        responses:
          200:
            description: Detailed experiment results and comparison table
            schema:
              type: object
              properties:
                experiment:
                  type: object
                comparison:
                  type: object
                  description: Per-metric, per-variant mean/std/count
                generated_at:
                  type: string
          401:
            description: Unauthorised
          403:
            description: Admin access required
          404:
            description: Experiment not found
        """
        ab_manager = get_ab_manager()
        results = ab_manager.get_results(experiment_name)

        if results is None:
            return {"error": f"Experiment '{experiment_name}' not found"}, 404

        # Enhance with variant comparison
        variants = results.get("variants", {})
        comparison = {}

        # Find all unique metrics across variants
        all_metrics = set()
        for variant_data in variants.values():
            all_metrics.update(variant_data.get("metrics", {}).keys())

        # Build comparison table
        for metric in all_metrics:
            comparison[metric] = {}
            for variant_name, variant_data in variants.items():
                metric_stats = variant_data.get("metrics", {}).get(metric, {})
                comparison[metric][variant_name] = {
                    "mean": metric_stats.get("mean", 0),
                    "std": metric_stats.get("std", 0),
                    "count": metric_stats.get("count", 0),
                }

        return {
            "experiment": results,
            "comparison": comparison,
            "generated_at": datetime.now().isoformat(),
        }, 200


class AdminSystemHealthResource(Resource):
    """Get detailed system health information."""

    @admin_required
    def get(self):
        """
        Get detailed system health for all components.
        ---
        tags:
          - Admin
        security:
          - Bearer: []
        responses:
          200:
            description: Component health status
            schema:
              type: object
              properties:
                status:
                  type: string
                  enum: [healthy, degraded, unhealthy]
                  example: healthy
                components:
                  type: object
                  properties:
                    content_based_model:
                      type: object
                    collaborative_model:
                      type: object
                    ab_testing:
                      type: object
                checked_at:
                  type: string
          401:
            description: Unauthorised
          403:
            description: Admin access required
        """
        content_rec = get_cached_recommender()
        cf_rec = get_cached_cf_recommender()

        # Check model health
        content_healthy = content_rec.is_loaded
        cf_healthy = cf_rec.is_loaded

        # Overall status
        overall_status = "healthy" if (content_healthy and cf_healthy) else "degraded"
        if not content_healthy and not cf_healthy:
            overall_status = "unhealthy"

        return {
            "status": overall_status,
            "components": {
                "content_based_model": {
                    "status": "healthy" if content_healthy else "unhealthy",
                    "loaded": content_healthy,
                    "info": content_rec.model_info,
                },
                "collaborative_model": {
                    "status": "healthy" if cf_healthy else "unhealthy",
                    "loaded": cf_healthy,
                    "info": cf_rec.model_info,
                },
                "ab_testing": {
                    "status": "healthy",
                    "experiments_count": len(get_ab_manager().list_experiments()),
                },
            },
            "checked_at": datetime.now().isoformat(),
        }, 200
