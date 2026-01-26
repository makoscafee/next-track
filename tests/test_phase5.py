"""
Tests for Phase 5: Hybrid Integration features.

Tests A/B testing framework, explanation generation, and diversity/serendipity controls.
"""

import pytest

from app.ml.ab_testing import (
    ABTestManager,
    Experiment,
    ExperimentStatus,
    Variant,
    create_default_experiments,
    get_ab_manager,
)
from app.ml.explainer import (
    Explanation,
    ExplanationType,
    FeatureContribution,
    RecommendationExplainer,
    get_explainer,
)
from app.ml.hybrid import HybridRecommender


class TestABTestingVariant:
    """Tests for A/B test Variant class."""

    def test_variant_creation(self):
        """Test creating a variant."""
        variant = Variant(name="control", weight=0.5, config={"test": "value"})
        assert variant.name == "control"
        assert variant.weight == 0.5
        assert variant.config == {"test": "value"}

    def test_variant_add_metric(self):
        """Test adding metrics to a variant."""
        variant = Variant(name="test", weight=1.0)
        variant.add_metric("click_rate", 0.5)
        variant.add_metric("click_rate", 0.7)
        assert len(variant.metrics["click_rate"]) == 2
        assert variant.metrics["click_rate"] == [0.5, 0.7]

    def test_variant_get_metric_stats(self):
        """Test getting metric statistics."""
        variant = Variant(name="test", weight=1.0)
        variant.add_metric("score", 0.4)
        variant.add_metric("score", 0.6)
        variant.add_metric("score", 0.8)

        stats = variant.get_metric_stats("score")
        assert stats["count"] == 3
        assert stats["mean"] == pytest.approx(0.6, abs=0.01)
        assert stats["min"] == 0.4
        assert stats["max"] == 0.8

    def test_variant_empty_metric_stats(self):
        """Test stats for non-existent metric."""
        variant = Variant(name="test", weight=1.0)
        stats = variant.get_metric_stats("nonexistent")
        assert stats["count"] == 0
        assert stats["mean"] == 0


class TestABTestingExperiment:
    """Tests for A/B test Experiment class."""

    def test_experiment_creation(self):
        """Test creating an experiment."""
        variants = [
            Variant(name="control", weight=0.5),
            Variant(name="treatment", weight=0.5),
        ]
        exp = Experiment(
            name="test_exp",
            description="Test experiment",
            variants=variants,
        )
        assert exp.name == "test_exp"
        assert exp.status == ExperimentStatus.DRAFT
        assert len(exp.variants) == 2

    def test_experiment_weight_normalization(self):
        """Test that variant weights are normalized."""
        variants = [
            Variant(name="a", weight=1.0),
            Variant(name="b", weight=1.0),
            Variant(name="c", weight=2.0),
        ]
        exp = Experiment(name="test", description="", variants=variants)
        total_weight = sum(v.weight for v in exp.variants)
        assert total_weight == pytest.approx(1.0, abs=0.01)

    def test_experiment_user_assignment_consistent(self):
        """Test that user assignment is consistent (deterministic)."""
        variants = [
            Variant(name="control", weight=0.5),
            Variant(name="treatment", weight=0.5),
        ]
        exp = Experiment(name="test", description="", variants=variants)

        # Same user should always get same variant
        user_id = "user_123"
        variant1 = exp.get_variant_for_user(user_id)
        variant2 = exp.get_variant_for_user(user_id)
        assert variant1.name == variant2.name

    def test_experiment_different_users_distributed(self):
        """Test that different users are distributed across variants."""
        variants = [
            Variant(name="control", weight=0.5),
            Variant(name="treatment", weight=0.5),
        ]
        exp = Experiment(name="test", description="", variants=variants)

        # Check that we get both variants across many users
        variant_names = set()
        for i in range(100):
            variant = exp.get_variant_for_user(f"user_{i}")
            variant_names.add(variant.name)

        assert "control" in variant_names
        assert "treatment" in variant_names

    def test_experiment_lifecycle(self):
        """Test experiment status transitions."""
        variants = [Variant(name="control", weight=1.0)]
        exp = Experiment(name="test", description="", variants=variants)

        assert exp.status == ExperimentStatus.DRAFT
        exp.start()
        assert exp.status == ExperimentStatus.RUNNING
        assert exp.started_at is not None

        exp.pause()
        assert exp.status == ExperimentStatus.PAUSED

        exp.complete()
        assert exp.status == ExperimentStatus.COMPLETED
        assert exp.ended_at is not None


class TestABTestManager:
    """Tests for ABTestManager class."""

    def test_manager_initialization(self):
        """Test manager initialization."""
        manager = ABTestManager()
        assert len(manager.experiments) == 0

    def test_create_experiment(self):
        """Test creating an experiment through manager."""
        manager = ABTestManager()
        exp = manager.create_experiment(
            name="test_exp",
            description="A test experiment",
            variants=[
                {"name": "control", "weight": 0.5, "config": {"param": 1}},
                {"name": "treatment", "weight": 0.5, "config": {"param": 2}},
            ],
        )

        assert exp.name == "test_exp"
        assert exp.status == ExperimentStatus.DRAFT
        assert "test_exp" in manager.experiments

    def test_create_experiment_auto_start(self):
        """Test auto-starting an experiment."""
        manager = ABTestManager()
        exp = manager.create_experiment(
            name="test",
            description="",
            variants=[{"name": "control", "weight": 1.0}],
            auto_start=True,
        )

        assert exp.status == ExperimentStatus.RUNNING

    def test_get_variant_not_running(self):
        """Test getting variant for non-running experiment."""
        manager = ABTestManager()
        manager.create_experiment(
            name="test",
            description="",
            variants=[{"name": "control", "weight": 1.0}],
            auto_start=False,
        )

        # Should return None for non-running experiment
        variant = manager.get_variant("test", "user_123")
        assert variant is None

    def test_get_variant_running(self):
        """Test getting variant for running experiment."""
        manager = ABTestManager()
        manager.create_experiment(
            name="test",
            description="",
            variants=[{"name": "control", "weight": 1.0, "config": {"value": 42}}],
            auto_start=True,
        )

        variant = manager.get_variant("test", "user_123")
        assert variant is not None
        assert variant.name == "control"
        assert variant.config["value"] == 42

    def test_record_metric(self):
        """Test recording metrics."""
        manager = ABTestManager()
        manager.create_experiment(
            name="test",
            description="",
            variants=[{"name": "control", "weight": 1.0}],
            auto_start=True,
        )

        manager.record_metric("test", "user_123", "click_rate", 1.0)
        manager.record_metric("test", "user_123", "click_rate", 0.5)

        results = manager.get_results("test")
        variant_results = results["variants"]["control"]
        assert variant_results["metrics"]["click_rate"]["count"] == 2

    def test_list_experiments(self):
        """Test listing experiments."""
        manager = ABTestManager()
        manager.create_experiment(
            name="exp1", description="First", variants=[{"name": "a", "weight": 1.0}]
        )
        manager.create_experiment(
            name="exp2", description="Second", variants=[{"name": "b", "weight": 1.0}]
        )

        experiments = manager.list_experiments()
        assert len(experiments) == 2
        names = [e["name"] for e in experiments]
        assert "exp1" in names
        assert "exp2" in names


class TestDefaultExperiments:
    """Tests for default experiment creation."""

    def test_create_default_experiments(self):
        """Test that default experiments are created correctly."""
        manager = ABTestManager()
        create_default_experiments(manager)

        assert "hybrid_weights" in manager.experiments
        assert "diversity_level" in manager.experiments
        assert "serendipity" in manager.experiments

    def test_default_experiments_running(self):
        """Test that default experiments are auto-started."""
        manager = ABTestManager()
        create_default_experiments(manager)

        for name in ["hybrid_weights", "diversity_level", "serendipity"]:
            exp = manager.get_experiment(name)
            assert exp.status == ExperimentStatus.RUNNING

    def test_get_ab_manager_singleton(self):
        """Test singleton pattern."""
        manager1 = get_ab_manager()
        manager2 = get_ab_manager()
        assert manager1 is manager2


class TestRecommendationExplainer:
    """Tests for recommendation explanation generation."""

    def test_explainer_initialization(self):
        """Test explainer initialization."""
        explainer = RecommendationExplainer()
        assert len(explainer.FEATURE_INFO) == 7
        assert "energy" in explainer.FEATURE_INFO
        assert "valence" in explainer.FEATURE_INFO

    def test_get_feature_level(self):
        """Test feature level categorization."""
        explainer = RecommendationExplainer()
        assert explainer._get_feature_level(0.8) == "high"
        assert explainer._get_feature_level(0.5) == "mid"
        assert explainer._get_feature_level(0.2) == "low"

    def test_calculate_feature_contribution(self):
        """Test feature contribution calculation."""
        explainer = RecommendationExplainer()
        contrib = explainer._calculate_feature_contribution("energy", 0.8, 0.75)

        assert contrib.feature == "energy"
        assert contrib.value == 0.8
        assert contrib.target_value == 0.75
        assert contrib.contribution_score > 0.9  # Close values = high contribution

    def test_explain_content_based(self):
        """Test content-based explanation."""
        explainer = RecommendationExplainer()
        track_features = {"energy": 0.7, "valence": 0.8, "danceability": 0.6}
        seed_features = {"energy": 0.75, "valence": 0.78, "danceability": 0.55}

        explanation = explainer.explain_content_based(
            track_id="track_123",
            track_features=track_features,
            seed_features=seed_features,
            similarity_score=0.92,
        )

        assert explanation.track_id == "track_123"
        assert explanation.primary_reason == ExplanationType.SIMILAR_AUDIO
        assert explanation.confidence == 0.92
        assert len(explanation.summary) > 0

    def test_explain_collaborative(self):
        """Test collaborative filtering explanation."""
        explainer = RecommendationExplainer()

        explanation = explainer.explain_collaborative(
            track_id="track_456",
            cf_score=0.85,
            similar_users_count=25,
        )

        assert explanation.track_id == "track_456"
        assert explanation.primary_reason == ExplanationType.SIMILAR_USERS
        assert "25" in explanation.summary

    def test_explain_mood_based(self):
        """Test mood-based explanation."""
        explainer = RecommendationExplainer()
        track_features = {"energy": 0.8, "valence": 0.75}

        explanation = explainer.explain_mood_based(
            track_id="track_789",
            mood="happy",
            mood_score=0.88,
            track_features=track_features,
        )

        assert explanation.track_id == "track_789"
        assert explanation.primary_reason == ExplanationType.MOOD_MATCH
        assert "happy" in explanation.summary.lower()

    def test_explain_mood_with_context(self):
        """Test mood explanation with context."""
        explainer = RecommendationExplainer()
        track_features = {"energy": 0.9, "valence": 0.7}
        context = {"time_of_day": "morning", "activity": "workout"}

        explanation = explainer.explain_mood_based(
            track_id="track_workout",
            mood="energetic",
            mood_score=0.9,
            track_features=track_features,
            context=context,
        )

        assert len(explanation.context_factors) > 0

    def test_explain_hybrid(self):
        """Test hybrid explanation."""
        explainer = RecommendationExplainer()
        model_scores = {"content": 0.85, "collaborative": 0.7, "sentiment": 0.6}
        model_weights = {"content": 0.4, "collaborative": 0.35, "sentiment": 0.25}

        explanation = explainer.explain_hybrid(
            track_id="track_hybrid",
            model_scores=model_scores,
            model_weights=model_weights,
        )

        assert explanation.track_id == "track_hybrid"
        assert explanation.confidence > 0
        assert len(explanation.model_contributions) == 3

    def test_format_explanation(self):
        """Test explanation formatting for API response."""
        explainer = RecommendationExplainer()

        explanation = Explanation(
            track_id="track_test",
            primary_reason=ExplanationType.SIMILAR_AUDIO,
            confidence=0.9,
            summary="Test summary",
            details=["Detail 1", "Detail 2"],
            feature_contributions=[],
            model_contributions={"content": 0.7, "collaborative": 0.3},
            context_factors=["morning music"],
        )

        formatted = explainer.format_explanation(explanation)

        assert formatted["track_id"] == "track_test"
        assert formatted["reason"] == "similar_audio"
        assert formatted["confidence"] == 0.9
        assert formatted["summary"] == "Test summary"
        assert "morning music" in formatted["context_factors"]

    def test_get_explainer_singleton(self):
        """Test singleton pattern."""
        explainer1 = get_explainer()
        explainer2 = get_explainer()
        assert explainer1 is explainer2


class TestHybridRecommenderPhase5:
    """Tests for Phase 5 enhancements to HybridRecommender."""

    def test_get_effective_weights_no_user(self):
        """Test effective weights without user (no A/B test)."""
        hybrid = HybridRecommender(
            content_weight=0.4, collab_weight=0.35, sentiment_weight=0.25
        )
        weights = hybrid.get_effective_weights()

        assert weights["content"] == 0.4
        assert weights["collaborative"] == 0.35
        assert weights["sentiment"] == 0.25

    def test_get_effective_weights_with_user(self):
        """Test effective weights with user (A/B test applies)."""
        hybrid = HybridRecommender()
        weights = hybrid.get_effective_weights(user_id="test_user")

        # Should get some weights (either default or from A/B test)
        assert "content" in weights
        assert "collaborative" in weights
        assert "sentiment" in weights
        total = sum(weights.values())
        assert total == pytest.approx(1.0, abs=0.01)

    def test_get_diversity_factor(self):
        """Test getting diversity factor."""
        hybrid = HybridRecommender()
        diversity = hybrid.get_diversity_factor()
        assert 0 <= diversity <= 1

    def test_get_serendipity_factor(self):
        """Test getting serendipity factor."""
        hybrid = HybridRecommender()
        serendipity = hybrid.get_serendipity_factor()
        assert 0 <= serendipity <= 1

    def test_feature_similarity(self):
        """Test feature similarity calculation."""
        hybrid = HybridRecommender()
        features1 = {
            "danceability": 0.8,
            "energy": 0.7,
            "valence": 0.6,
            "acousticness": 0.3,
        }
        features2 = {
            "danceability": 0.75,
            "energy": 0.72,
            "valence": 0.58,
            "acousticness": 0.35,
        }

        similarity = hybrid._feature_similarity(features1, features2)
        assert 0.9 < similarity <= 1.0  # Should be high for similar features

    def test_feature_similarity_different(self):
        """Test feature similarity for different features."""
        hybrid = HybridRecommender()
        features1 = {
            "danceability": 0.9,
            "energy": 0.9,
            "valence": 0.9,
            "acousticness": 0.1,
        }
        features2 = {
            "danceability": 0.1,
            "energy": 0.1,
            "valence": 0.1,
            "acousticness": 0.9,
        }

        similarity = hybrid._feature_similarity(features1, features2)
        assert similarity < 0.5  # Should be low for different features

    def test_record_feedback(self):
        """Test recording feedback."""
        hybrid = HybridRecommender()
        # Should not raise any exceptions
        hybrid.record_feedback("user_123", "track_456", "click", 1.0)
        hybrid.record_feedback("user_123", "track_456", "play", 1.0)

    def test_get_ab_results(self):
        """Test getting A/B test results."""
        hybrid = HybridRecommender()
        results = hybrid.get_ab_results("hybrid_weights")

        assert results is not None
        assert "experiment" in results
        assert "variants" in results

    def test_list_experiments(self):
        """Test listing experiments."""
        hybrid = HybridRecommender()
        experiments = hybrid.list_experiments()

        assert len(experiments) >= 3
        names = [e["name"] for e in experiments]
        assert "hybrid_weights" in names
        assert "diversity_level" in names
        assert "serendipity" in names


class TestAPIExperimentsEndpoints:
    """Tests for A/B testing API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from app import create_app

        app = create_app("testing")
        with app.test_client() as client:
            yield client

    def test_list_experiments(self, client):
        """Test listing experiments endpoint."""
        response = client.get("/api/v1/experiments")
        assert response.status_code == 200

        data = response.get_json()
        assert "experiments" in data
        assert "count" in data
        assert data["count"] >= 3

    def test_get_experiment_details(self, client):
        """Test getting experiment details."""
        response = client.get("/api/v1/experiments/hybrid_weights")
        assert response.status_code == 200

        data = response.get_json()
        assert data["experiment"] == "hybrid_weights"
        assert "variants" in data

    def test_get_experiment_not_found(self, client):
        """Test getting non-existent experiment."""
        response = client.get("/api/v1/experiments/nonexistent")
        assert response.status_code == 404

    def test_get_variant_assignment(self, client):
        """Test getting variant assignment for a user."""
        response = client.get(
            "/api/v1/experiments/hybrid_weights/variant?user_id=test_user"
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data["experiment"] == "hybrid_weights"
        assert data["user_id"] == "test_user"
        assert "variant" in data
        assert "name" in data["variant"]

    def test_get_variant_missing_user_id(self, client):
        """Test getting variant without user_id."""
        response = client.get("/api/v1/experiments/hybrid_weights/variant")
        assert response.status_code == 400

    def test_record_metric(self, client):
        """Test recording a metric."""
        response = client.post(
            "/api/v1/experiments/hybrid_weights/metrics",
            json={
                "user_id": "test_user",
                "metric_name": "click_rate",
                "value": 0.75,
            },
        )
        assert response.status_code == 201

        data = response.get_json()
        assert data["status"] == "recorded"

    def test_record_metric_missing_fields(self, client):
        """Test recording metric with missing fields."""
        response = client.post(
            "/api/v1/experiments/hybrid_weights/metrics",
            json={"user_id": "test_user"},
        )
        assert response.status_code == 400

    def test_record_feedback(self, client):
        """Test recording user feedback."""
        response = client.post(
            "/api/v1/feedback",
            json={
                "user_id": "test_user",
                "track_id": "track_123",
                "feedback_type": "click",
            },
        )
        assert response.status_code == 201

        data = response.get_json()
        assert data["status"] == "recorded"

    def test_record_feedback_invalid_type(self, client):
        """Test recording feedback with invalid type."""
        response = client.post(
            "/api/v1/feedback",
            json={
                "user_id": "test_user",
                "track_id": "track_123",
                "feedback_type": "invalid_type",
            },
        )
        assert response.status_code == 400


class TestRecommendEndpointPhase5:
    """Tests for enhanced recommendation endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from app import create_app

        app = create_app("testing")
        with app.test_client() as client:
            yield client

    def test_recommend_with_diversity_factor(self, client):
        """Test recommendation with diversity factor."""
        response = client.post(
            "/api/v1/recommend",
            json={
                "mood": "happy",
                "limit": 5,
                "diversity_factor": 0.5,
            },
        )
        assert response.status_code == 200

    def test_recommend_with_serendipity_factor(self, client):
        """Test recommendation with serendipity factor."""
        response = client.post(
            "/api/v1/recommend",
            json={
                "mood": "energetic",
                "limit": 5,
                "serendipity_factor": 0.2,
            },
        )
        assert response.status_code == 200

    def test_recommend_with_explanation(self, client):
        """Test recommendation with explanation request."""
        response = client.post(
            "/api/v1/recommend",
            json={
                "mood": "calm",
                "limit": 5,
                "include_explanation": True,
            },
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data["metadata"]["explanations_included"] is True

    def test_recommend_invalid_diversity_factor(self, client):
        """Test recommendation with invalid diversity factor."""
        response = client.post(
            "/api/v1/recommend",
            json={
                "mood": "happy",
                "diversity_factor": 1.5,  # Invalid: > 1
            },
        )
        assert response.status_code == 400

    def test_recommend_invalid_serendipity_factor(self, client):
        """Test recommendation with invalid serendipity factor."""
        response = client.post(
            "/api/v1/recommend",
            json={
                "mood": "happy",
                "serendipity_factor": -0.1,  # Invalid: < 0
            },
        )
        assert response.status_code == 400
