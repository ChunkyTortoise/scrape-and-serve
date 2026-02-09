"""Data quality profiling, schema validation, and outlier detection."""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass, field


@dataclass
class ColumnProfile:
    """Profile of a single data column."""

    name: str
    dtype: str
    null_count: int
    null_ratio: float
    unique_count: int
    cardinality_ratio: float
    min_value: object = None
    max_value: object = None
    mean: float | None = None
    std: float | None = None


@dataclass
class DataProfile:
    """Profile of an entire dataset."""

    columns: list[ColumnProfile]
    row_count: int
    completeness_score: float


@dataclass
class SchemaRule:
    """Expected schema rule for a column."""

    column: str
    expected_type: str
    required: bool = True
    min_value: float | None = None
    max_value: float | None = None


@dataclass
class ValidationReport:
    """Result of schema validation."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class OutlierReport:
    """Result of outlier detection."""

    outlier_indices: list[int]
    lower_fence: float
    upper_fence: float
    outlier_count: int


@dataclass
class QualityReport:
    """Comprehensive data quality assessment."""

    profile: DataProfile
    validation: ValidationReport
    outlier_reports: dict[str, OutlierReport]
    overall_score: float
    recommendations: list[str]


_DATE_PATTERNS = [
    re.compile(r"^\d{4}-\d{2}-\d{2}$"),
    re.compile(r"^\d{2}/\d{2}/\d{4}$"),
    re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}"),
]


def _detect_type(values: list) -> str:
    """Auto-detect column type from non-None values."""
    non_null = [v for v in values if v is not None]
    if not non_null:
        return "unknown"

    # Check booleans first (before numeric, since bool is subclass of int)
    if all(isinstance(v, bool) for v in non_null):
        return "boolean"

    # Check numeric (int or float, but not bool)
    if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in non_null):
        return "numeric"

    # Check date-like strings
    str_vals = [v for v in non_null if isinstance(v, str)]
    if str_vals and len(str_vals) == len(non_null):
        date_matches = sum(1 for v in str_vals if any(p.match(v) for p in _DATE_PATTERNS))
        if date_matches > len(str_vals) * 0.5:
            return "date"

    # Default to string
    if all(isinstance(v, str) for v in non_null):
        return "string"

    return "mixed"


class DataProfiler:
    """Auto-profile tabular data."""

    def profile(self, data: list[dict]) -> DataProfile:
        """Profile a list of row dicts."""
        if not data:
            return DataProfile(columns=[], row_count=0, completeness_score=1.0)

        all_keys: list[str] = []
        seen: set[str] = set()
        for row in data:
            for k in row:
                if k not in seen:
                    all_keys.append(k)
                    seen.add(k)

        row_count = len(data)
        total_cells = row_count * len(all_keys) if all_keys else 1
        non_null_cells = 0
        columns: list[ColumnProfile] = []

        for key in all_keys:
            values = [row.get(key) for row in data]
            non_nulls = [v for v in values if v is not None]
            null_count = row_count - len(non_nulls)
            non_null_cells += len(non_nulls)
            null_ratio = null_count / row_count if row_count > 0 else 0.0
            unique_count = len(set(str(v) for v in non_nulls))
            cardinality_ratio = unique_count / len(non_nulls) if non_nulls else 0.0

            dtype = _detect_type(values)

            col = ColumnProfile(
                name=key,
                dtype=dtype,
                null_count=null_count,
                null_ratio=null_ratio,
                unique_count=unique_count,
                cardinality_ratio=cardinality_ratio,
            )

            if dtype == "numeric" and non_nulls:
                numeric_vals = [v for v in non_nulls if isinstance(v, (int, float))]
                if numeric_vals:
                    col.min_value = min(numeric_vals)
                    col.max_value = max(numeric_vals)
                    col.mean = statistics.mean(numeric_vals)
                    col.std = statistics.stdev(numeric_vals) if len(numeric_vals) > 1 else 0.0
            elif dtype == "string" and non_nulls:
                str_vals = sorted(str(v) for v in non_nulls)
                col.min_value = str_vals[0]
                col.max_value = str_vals[-1]

            columns.append(col)

        completeness = non_null_cells / total_cells if total_cells > 0 else 1.0

        return DataProfile(
            columns=columns,
            row_count=row_count,
            completeness_score=round(completeness, 4),
        )


class SchemaValidator:
    """Validate data against expected schema rules."""

    def validate(self, data: list[dict], rules: list[SchemaRule]) -> ValidationReport:
        """Validate all rows against schema rules."""
        errors: list[str] = []
        warnings: list[str] = []

        for rule in rules:
            values = [row.get(rule.column) for row in data]
            non_null = [v for v in values if v is not None]
            null_count = len(values) - len(non_null)

            if rule.required and null_count > 0:
                errors.append(f"Column '{rule.column}' has {null_count} missing values but is required")

            type_map = {
                "numeric": (int, float),
                "string": (str,),
                "boolean": (bool,),
            }
            expected_types = type_map.get(rule.expected_type)
            if expected_types and non_null:
                bad = [
                    v
                    for v in non_null
                    if not isinstance(v, expected_types) or (rule.expected_type != "boolean" and isinstance(v, bool))
                ]
                if bad:
                    errors.append(
                        f"Column '{rule.column}' has {len(bad)} values with wrong type (expected {rule.expected_type})"
                    )

            if rule.min_value is not None and non_null:
                below = [
                    v
                    for v in non_null
                    if isinstance(v, (int, float)) and not isinstance(v, bool) and v < rule.min_value
                ]
                if below:
                    warnings.append(f"Column '{rule.column}' has {len(below)} values below minimum {rule.min_value}")

            if rule.max_value is not None and non_null:
                above = [
                    v
                    for v in non_null
                    if isinstance(v, (int, float)) and not isinstance(v, bool) and v > rule.max_value
                ]
                if above:
                    warnings.append(f"Column '{rule.column}' has {len(above)} values above maximum {rule.max_value}")

        return ValidationReport(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


class OutlierDetector:
    """Tukey's fences (IQR-based) outlier detection."""

    def detect(self, values: list[float], multiplier: float = 1.5) -> OutlierReport:
        """Detect outliers using IQR method."""
        if len(values) < 4:
            return OutlierReport(
                outlier_indices=[],
                lower_fence=min(values) if values else 0.0,
                upper_fence=max(values) if values else 0.0,
                outlier_count=0,
            )

        sorted_vals = sorted(values)
        n = len(sorted_vals)
        q1 = sorted_vals[n // 4]
        q3 = sorted_vals[(3 * n) // 4]
        iqr = q3 - q1

        lower_fence = q1 - multiplier * iqr
        upper_fence = q3 + multiplier * iqr

        outlier_indices = [i for i, v in enumerate(values) if v < lower_fence or v > upper_fence]

        return OutlierReport(
            outlier_indices=outlier_indices,
            lower_fence=lower_fence,
            upper_fence=upper_fence,
            outlier_count=len(outlier_indices),
        )


class QualityEngine:
    """Comprehensive data quality assessment."""

    def __init__(self) -> None:
        self._profiler = DataProfiler()
        self._validator = SchemaValidator()
        self._outlier_detector = OutlierDetector()

    def assess(
        self,
        data: list[dict],
        schema_rules: list[SchemaRule] | None = None,
    ) -> QualityReport:
        """Run full quality assessment on data."""
        profile = self._profiler.profile(data)

        if schema_rules:
            validation = self._validator.validate(data, schema_rules)
        else:
            validation = ValidationReport(valid=True)

        outlier_reports: dict[str, OutlierReport] = {}
        for col in profile.columns:
            if col.dtype == "numeric":
                values = [
                    row.get(col.name)
                    for row in data
                    if row.get(col.name) is not None
                    and isinstance(row.get(col.name), (int, float))
                    and not isinstance(row.get(col.name), bool)
                ]
                if len(values) >= 4:
                    outlier_reports[col.name] = self._outlier_detector.detect(values)

        recommendations = self._generate_recommendations(profile, validation, outlier_reports)

        # Overall score: weighted combination
        completeness_weight = 0.4
        validity_weight = 0.4
        outlier_weight = 0.2

        completeness_score = profile.completeness_score
        validity_score = 1.0 if validation.valid else max(0.0, 1.0 - len(validation.errors) * 0.1)

        if outlier_reports:
            total_values = sum(len([r.get(col) for r in data if r.get(col) is not None]) for col in outlier_reports)
            total_outliers = sum(r.outlier_count for r in outlier_reports.values())
            outlier_score = 1.0 - (total_outliers / total_values) if total_values > 0 else 1.0
        else:
            outlier_score = 1.0

        overall = (
            completeness_weight * completeness_score + validity_weight * validity_score + outlier_weight * outlier_score
        )

        return QualityReport(
            profile=profile,
            validation=validation,
            outlier_reports=outlier_reports,
            overall_score=round(overall, 4),
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self,
        profile: DataProfile,
        validation: ValidationReport,
        outlier_reports: dict[str, OutlierReport],
    ) -> list[str]:
        """Auto-generate recommendations based on findings."""
        recs: list[str] = []

        if profile.completeness_score < 0.9:
            recs.append("Data completeness is below 90%; consider imputing or collecting missing values")

        for col in profile.columns:
            if col.null_ratio > 0.5:
                recs.append(f"Column '{col.name}' is over 50% null; consider dropping or imputing")
            if col.dtype == "numeric" and col.cardinality_ratio < 0.01 and col.unique_count > 0:
                recs.append(f"Column '{col.name}' has very low cardinality; may be categorical")

        if not validation.valid:
            recs.append(f"Schema validation found {len(validation.errors)} error(s); review data pipeline")

        for col_name, report in outlier_reports.items():
            if report.outlier_count > 0:
                recs.append(f"Column '{col_name}' has {report.outlier_count} outlier(s); review for data errors")

        return recs
