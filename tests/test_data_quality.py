"""Tests for data quality and preprocessing module."""

import numpy as np
import pandas as pd
import pytest

from app.ml.data_quality import (
    ALL_AUDIO_FEATURES,
    CONTENT_MODEL_FEATURES,
    FEATURE_RANGES,
    DataPreprocessor,
    DataValidator,
    OutlierDetector,
)


@pytest.fixture
def sample_tracks_df():
    """Create a sample tracks DataFrame with realistic audio features."""
    np.random.seed(42)
    n = 200
    return pd.DataFrame(
        {
            "id": [f"track_{i}" for i in range(n)],
            "name": [f"Song {i}" for i in range(n)],
            "artists": [f"Artist {i % 20}" for i in range(n)],
            "danceability": np.random.uniform(0, 1, n),
            "energy": np.random.uniform(0, 1, n),
            "valence": np.random.uniform(0, 1, n),
            "tempo": np.random.uniform(60, 200, n),
            "acousticness": np.random.uniform(0, 1, n),
            "instrumentalness": np.random.uniform(0, 1, n),
            "speechiness": np.random.uniform(0, 1, n),
            "liveness": np.random.uniform(0, 1, n),
            "loudness": np.random.uniform(-40, -3, n),
            "key": np.random.randint(0, 12, n).astype(float),
            "mode": np.random.randint(0, 2, n).astype(float),
        }
    )


@pytest.fixture
def dirty_tracks_df(sample_tracks_df):
    """Create a dirty DataFrame with nulls, duplicates, and outliers."""
    df = sample_tracks_df.copy()
    # Add nulls
    df.loc[0:4, "danceability"] = np.nan
    df.loc[5:7, "energy"] = np.nan
    df.loc[8, "valence"] = np.nan
    # Add duplicate
    dup_row = df.iloc[[10]].copy()
    df = pd.concat([df, dup_row], ignore_index=True)
    # Add outliers
    df.loc[10, "tempo"] = 500.0
    df.loc[11, "loudness"] = 10.0
    return df


class TestDataValidator:
    def test_validate_clean_data(self, sample_tracks_df):
        validator = DataValidator()
        report = validator.validate(sample_tracks_df)
        assert report["valid"] is True
        assert len(report["errors"]) == 0
        assert report["total_rows"] == 200

    def test_validate_missing_id_column(self, sample_tracks_df):
        df = sample_tracks_df.drop(columns=["id"])
        validator = DataValidator()
        report = validator.validate(df)
        assert report["valid"] is False
        assert any("'id'" in e for e in report["errors"])

    def test_validate_missing_feature_column(self, sample_tracks_df):
        df = sample_tracks_df.drop(columns=["danceability"])
        validator = DataValidator()
        report = validator.validate(df)
        assert report["valid"] is False
        assert "danceability" in report["missing_columns"]

    def test_validate_nulls_reported(self, dirty_tracks_df):
        validator = DataValidator()
        report = validator.validate(dirty_tracks_df)
        assert report["null_report"]["danceability"]["count"] == 5
        assert report["null_report"]["energy"]["count"] == 3
        assert report["null_report"]["valence"]["count"] == 1

    def test_validate_range_violations(self, dirty_tracks_df):
        validator = DataValidator()
        report = validator.validate(dirty_tracks_df)
        assert report["range_violations"]["tempo"]["above"] >= 1
        assert report["range_violations"]["loudness"]["above"] >= 1

    def test_validate_type_issues(self, sample_tracks_df):
        df = sample_tracks_df.copy()
        df["energy"] = "not_numeric"
        validator = DataValidator()
        report = validator.validate(df)
        assert report["valid"] is False
        assert "energy" in report["type_issues"]

    def test_validate_with_subset_features(self, sample_tracks_df):
        validator = DataValidator(features=CONTENT_MODEL_FEATURES)
        report = validator.validate(sample_tracks_df)
        assert report["valid"] is True
        # Only checks the 7 content model features
        assert len(report["null_report"]) == len(CONTENT_MODEL_FEATURES)


class TestOutlierDetector:
    def test_detect_returns_report(self, sample_tracks_df):
        detector = OutlierDetector()
        report = detector.detect(sample_tracks_df)
        assert "danceability" in report
        assert "q1" in report["danceability"]
        assert "outlier_count" in report["danceability"]

    def test_detect_with_outliers(self, dirty_tracks_df):
        detector = OutlierDetector()
        report = detector.detect(dirty_tracks_df)
        # Tempo 500 should be detected as outlier
        assert report["tempo"]["outlier_count"] >= 1

    def test_clip_outliers(self, dirty_tracks_df):
        detector = OutlierDetector()
        clipped = detector.clip_outliers(dirty_tracks_df)
        # Tempo should be clipped to within range
        assert clipped["tempo"].max() <= 250.0

    def test_clip_respects_natural_bounds(self):
        """IQR fence beyond [0,1] should clip to natural bound."""
        df = pd.DataFrame(
            {
                "danceability": [0.5] * 100 + [1.5],
                "energy": [0.5] * 100 + [0.6],
            }
        )
        detector = OutlierDetector(features=["danceability", "energy"])
        clipped = detector.clip_outliers(df)
        assert clipped["danceability"].max() <= 1.0

    def test_returns_copy(self, sample_tracks_df):
        detector = OutlierDetector()
        original_tempo = sample_tracks_df["tempo"].copy()
        _ = detector.clip_outliers(sample_tracks_df)
        pd.testing.assert_series_equal(sample_tracks_df["tempo"], original_tempo)


class TestDataPreprocessor:
    def test_preprocess_clean_data(self, sample_tracks_df):
        preprocessor = DataPreprocessor(handle_outliers=False)
        result, report = preprocessor.preprocess(sample_tracks_df)
        assert report["input_rows"] == 200
        assert report["duplicates_removed"] == 0
        assert report["rows_filtered_missing"] == 0
        assert report["output_rows"] == 200

    def test_removes_duplicates(self, dirty_tracks_df):
        preprocessor = DataPreprocessor(
            max_missing_features=None, handle_outliers=False
        )
        result, report = preprocessor.preprocess(dirty_tracks_df)
        assert report["duplicates_removed"] == 1
        assert result["id"].is_unique

    def test_filters_rows_with_many_missing(self):
        df = pd.DataFrame(
            {
                "id": ["a", "b", "c"],
                "danceability": [0.5, np.nan, np.nan],
                "energy": [0.5, 0.5, np.nan],
                "valence": [0.5, np.nan, np.nan],
                "tempo": [120, 120, np.nan],
                "acousticness": [0.5, 0.5, 0.5],
                "instrumentalness": [0.5, 0.5, 0.5],
                "speechiness": [0.5, 0.5, 0.5],
                "liveness": [0.5, 0.5, 0.5],
                "loudness": [-10, -10, -10],
                "key": [1, 1, 1],
                "mode": [1, 1, 1],
            }
        )
        # a: 0 missing, b: 2 missing (ok), c: 4 missing (filtered)
        preprocessor = DataPreprocessor(max_missing_features=2, handle_outliers=False)
        result, report = preprocessor.preprocess(df)
        assert "a" in result["id"].values
        assert "b" in result["id"].values
        assert "c" not in result["id"].values
        assert report["rows_filtered_missing"] == 1

    def test_median_imputation(self, dirty_tracks_df):
        preprocessor = DataPreprocessor(
            max_missing_features=None, handle_outliers=False
        )
        result, report = preprocessor.preprocess(dirty_tracks_df)
        assert result["danceability"].isna().sum() == 0
        assert result["energy"].isna().sum() == 0
        assert "danceability" in report["imputation"]
        assert report["imputation"]["danceability"]["count"] == 5

    def test_tempo_normalization(self, sample_tracks_df):
        preprocessor = DataPreprocessor(handle_outliers=False)
        result, report = preprocessor.preprocess(sample_tracks_df)
        assert result["tempo"].max() <= 1.0
        assert result["tempo"].min() >= 0.0
        assert report["tempo_normalized"] is True
        assert "tempo_normalized" in result.columns

    def test_feature_clipping(self):
        df = pd.DataFrame(
            {
                "id": ["a"],
                "danceability": [1.5],
                "energy": [-0.1],
                "valence": [0.5],
                "tempo": [120],
                "acousticness": [0.5],
                "instrumentalness": [0.5],
                "speechiness": [0.5],
                "liveness": [0.5],
                "loudness": [-10],
                "key": [1],
                "mode": [1],
            }
        )
        preprocessor = DataPreprocessor(handle_outliers=False)
        result, _ = preprocessor.preprocess(df)
        assert result["danceability"].iloc[0] == 1.0
        assert result["energy"].iloc[0] == 0.0

    def test_outlier_handling(self, dirty_tracks_df):
        preprocessor = DataPreprocessor(
            max_missing_features=None, handle_outliers=True
        )
        result, report = preprocessor.preprocess(dirty_tracks_df)
        assert report["outliers"] is not None
        # Tempo was 500 — after outlier clipping + tempo normalization, should be <= 1
        assert result["tempo"].max() <= 1.0

    def test_no_mutation(self, sample_tracks_df):
        original = sample_tracks_df.copy()
        preprocessor = DataPreprocessor()
        _ = preprocessor.preprocess(sample_tracks_df)
        pd.testing.assert_frame_equal(sample_tracks_df, original)

    def test_quality_report_structure(self, sample_tracks_df):
        preprocessor = DataPreprocessor()
        _, report = preprocessor.preprocess(sample_tracks_df)
        expected_keys = {
            "input_rows",
            "duplicates_removed",
            "rows_filtered_missing",
            "output_rows",
            "imputation",
            "outliers",
            "validation",
            "tempo_normalized",
        }
        assert expected_keys == set(report.keys())

    def test_skip_validation(self, sample_tracks_df):
        preprocessor = DataPreprocessor()
        _, report = preprocessor.preprocess(sample_tracks_df, validate=False)
        assert report["validation"] is None

    def test_max_missing_none_keeps_all(self, dirty_tracks_df):
        preprocessor = DataPreprocessor(
            max_missing_features=None, handle_outliers=False
        )
        result, report = preprocessor.preprocess(dirty_tracks_df)
        assert report["rows_filtered_missing"] == 0
