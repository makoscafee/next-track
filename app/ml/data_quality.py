"""
Data quality validation, outlier detection, and preprocessing pipeline
for audio features in the Kaggle Spotify dataset.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# All 11 audio features in the dataset
ALL_AUDIO_FEATURES = [
    "danceability",
    "energy",
    "valence",
    "tempo",
    "acousticness",
    "instrumentalness",
    "speechiness",
    "liveness",
    "loudness",
    "key",
    "mode",
]

# The 7 features used by the content-based model
CONTENT_MODEL_FEATURES = [
    "danceability",
    "energy",
    "valence",
    "tempo",
    "acousticness",
    "instrumentalness",
    "speechiness",
]

# Expected value ranges before normalization
FEATURE_RANGES = {
    "danceability": (0.0, 1.0),
    "energy": (0.0, 1.0),
    "valence": (0.0, 1.0),
    "acousticness": (0.0, 1.0),
    "instrumentalness": (0.0, 1.0),
    "speechiness": (0.0, 1.0),
    "liveness": (0.0, 1.0),
    "tempo": (0.0, 250.0),
    "loudness": (-60.0, 0.0),
    "key": (0, 11),
    "mode": (0, 1),
}

# Features that are continuous 0-1 range (suitable for IQR outlier detection)
_CONTINUOUS_FEATURES = [
    "danceability",
    "energy",
    "valence",
    "tempo",
    "acousticness",
    "instrumentalness",
    "speechiness",
    "liveness",
    "loudness",
]


class DataValidator:
    """
    Validates a tracks DataFrame for required columns, types, ranges, and nulls.
    Returns a report dict — does not modify data.
    """

    def __init__(self, features: Optional[List[str]] = None):
        self.features = features or ALL_AUDIO_FEATURES

    def validate(self, df: pd.DataFrame) -> Dict:
        errors = []
        warnings = []

        # Check required columns
        missing_columns = self._check_required_columns(df)
        if "id" in missing_columns:
            errors.append("Missing required column: 'id'")
        for col in missing_columns:
            if col != "id":
                errors.append(f"Missing audio feature column: '{col}'")

        present_features = [f for f in self.features if f in df.columns]

        # Check data types
        type_issues = self._check_data_types(df, present_features)
        for feature, issue in type_issues.items():
            errors.append(f"Type issue in '{feature}': {issue}")

        # Check nulls
        null_report = self._check_nulls(df, present_features)
        for feature, info in null_report.items():
            if info["count"] > 0:
                warnings.append(
                    f"'{feature}' has {info['count']} null values ({info['pct']:.2f}%)"
                )

        # Check ranges
        range_violations = self._check_ranges(df, present_features)
        for feature, info in range_violations.items():
            total = info["below"] + info["above"]
            if total > 0:
                warnings.append(
                    f"'{feature}' has {total} values outside expected range "
                    f"{FEATURE_RANGES.get(feature, 'unknown')}"
                )

        valid = len(errors) == 0

        report = {
            "valid": valid,
            "total_rows": len(df),
            "errors": errors,
            "warnings": warnings,
            "missing_columns": missing_columns,
            "null_report": null_report,
            "range_violations": range_violations,
            "type_issues": type_issues,
        }

        if valid:
            logger.info(
                f"Validation passed: {len(df)} rows, {len(warnings)} warnings"
            )
        else:
            logger.warning(
                f"Validation failed: {len(errors)} errors, {len(warnings)} warnings"
            )

        return report

    def _check_required_columns(self, df: pd.DataFrame) -> List[str]:
        required = ["id"] + self.features
        return [col for col in required if col not in df.columns]

    def _check_data_types(
        self, df: pd.DataFrame, features: List[str]
    ) -> Dict[str, str]:
        issues = {}
        for feature in features:
            if not pd.api.types.is_numeric_dtype(df[feature]):
                issues[feature] = f"expected numeric, got {df[feature].dtype}"
        return issues

    def _check_nulls(
        self, df: pd.DataFrame, features: List[str]
    ) -> Dict[str, Dict]:
        report = {}
        for feature in features:
            count = int(df[feature].isna().sum())
            pct = (count / len(df)) * 100 if len(df) > 0 else 0.0
            report[feature] = {"count": count, "pct": pct}
        return report

    def _check_ranges(
        self, df: pd.DataFrame, features: List[str]
    ) -> Dict[str, Dict]:
        violations = {}
        for feature in features:
            if feature not in FEATURE_RANGES:
                continue
            if not pd.api.types.is_numeric_dtype(df[feature]):
                continue
            low, high = FEATURE_RANGES[feature]
            col = df[feature].dropna()
            below = int((col < low).sum())
            above = int((col > high).sum())
            violations[feature] = {"below": below, "above": above}
        return violations


class OutlierDetector:
    """
    IQR-based outlier detection for audio features.
    Can report or clip outliers, but never removes rows.
    """

    def __init__(
        self,
        iqr_multiplier: float = 1.5,
        features: Optional[List[str]] = None,
    ):
        self.iqr_multiplier = iqr_multiplier
        self.features = features or _CONTINUOUS_FEATURES

    def detect(self, df: pd.DataFrame) -> Dict[str, Dict]:
        report = {}
        for feature in self.features:
            if feature not in df.columns:
                continue
            col = df[feature].dropna()
            q1 = float(col.quantile(0.25))
            q3 = float(col.quantile(0.75))
            iqr = q3 - q1
            lower_fence = q1 - self.iqr_multiplier * iqr
            upper_fence = q3 + self.iqr_multiplier * iqr
            outlier_count = int(((col < lower_fence) | (col > upper_fence)).sum())
            outlier_pct = (outlier_count / len(col)) * 100 if len(col) > 0 else 0.0

            report[feature] = {
                "q1": q1,
                "q3": q3,
                "iqr": iqr,
                "lower_fence": lower_fence,
                "upper_fence": upper_fence,
                "outlier_count": outlier_count,
                "outlier_pct": outlier_pct,
            }

        return report

    def clip_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for feature in self.features:
            if feature not in df.columns:
                continue
            col = df[feature].dropna()
            q1 = col.quantile(0.25)
            q3 = col.quantile(0.75)
            iqr = q3 - q1
            lower_fence = q1 - self.iqr_multiplier * iqr
            upper_fence = q3 + self.iqr_multiplier * iqr

            # Respect natural bounds
            if feature in FEATURE_RANGES:
                natural_low, natural_high = FEATURE_RANGES[feature]
                lower_fence = max(lower_fence, natural_low)
                upper_fence = min(upper_fence, natural_high)

            df[feature] = df[feature].clip(lower_fence, upper_fence)

        return df


class DataPreprocessor:
    """
    Unified preprocessing pipeline that replaces both DatasetService._clean_data()
    and train_content_model.preprocess_features().
    """

    def __init__(
        self,
        features: Optional[List[str]] = None,
        max_missing_features: Optional[int] = 2,
        handle_outliers: bool = True,
        iqr_multiplier: float = 1.5,
    ):
        self.features = features or ALL_AUDIO_FEATURES
        self.max_missing_features = max_missing_features
        self.handle_outliers = handle_outliers
        self.iqr_multiplier = iqr_multiplier

    def preprocess(
        self, df: pd.DataFrame, validate: bool = True
    ) -> Tuple[pd.DataFrame, Dict]:
        df = df.copy()
        report = {
            "input_rows": len(df),
            "duplicates_removed": 0,
            "rows_filtered_missing": 0,
            "output_rows": 0,
            "imputation": {},
            "outliers": None,
            "validation": None,
            "tempo_normalized": False,
        }

        # Step 1: Validate
        if validate:
            validator = DataValidator(features=self.features)
            report["validation"] = validator.validate(df)

        # Step 2: Remove duplicates
        if "id" in df.columns:
            before = len(df)
            df = df.drop_duplicates(subset=["id"])
            report["duplicates_removed"] = before - len(df)

        # Step 3: Filter rows with too many missing features
        present_features = [f for f in self.features if f in df.columns]
        if self.max_missing_features is not None and present_features:
            missing_count = df[present_features].isna().sum(axis=1)
            before = len(df)
            df = df[missing_count <= self.max_missing_features].copy()
            report["rows_filtered_missing"] = before - len(df)

        # Step 4: Median imputation
        for feature in present_features:
            null_count = int(df[feature].isna().sum())
            if null_count > 0:
                median_val = float(df[feature].median())
                df[feature] = df[feature].fillna(median_val)
                report["imputation"][feature] = {
                    "count": null_count,
                    "median_value": median_val,
                }
                logger.info(
                    f"Imputed {null_count} missing values in '{feature}' with median {median_val:.4f}"
                )

        # Step 5: Outlier clipping
        if self.handle_outliers:
            detector = OutlierDetector(
                iqr_multiplier=self.iqr_multiplier,
                features=[f for f in present_features if f in _CONTINUOUS_FEATURES],
            )
            report["outliers"] = detector.detect(df)
            df = detector.clip_outliers(df)

        # Step 6: Normalize tempo
        if "tempo" in df.columns:
            max_tempo = df["tempo"].max()
            if max_tempo > 1:
                df["tempo"] = df["tempo"].clip(0, 250) / 250.0
                df["tempo_normalized"] = df["tempo"]
                report["tempo_normalized"] = True

        # Step 7: Clip 0-1 features
        zero_one_features = [
            f for f in present_features
            if f != "tempo" and FEATURE_RANGES.get(f) == (0.0, 1.0)
        ]
        for feature in zero_one_features:
            df[feature] = df[feature].clip(0.0, 1.0)

        report["output_rows"] = len(df)
        logger.info(
            f"Preprocessing complete: {report['input_rows']} -> {report['output_rows']} rows "
            f"({report['duplicates_removed']} duplicates, "
            f"{report['rows_filtered_missing']} filtered for missing features)"
        )

        return df, report
