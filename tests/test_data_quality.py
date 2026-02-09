"""Tests for the data quality & profiling module."""

from __future__ import annotations

from scrape_and_serve.data_quality import (
    DataProfiler,
    OutlierDetector,
    QualityEngine,
    QualityReport,
    SchemaRule,
    SchemaValidator,
)


class TestDataProfiler:
    def test_empty_data(self):
        profiler = DataProfiler()
        result = profiler.profile([])
        assert result.row_count == 0
        assert result.columns == []
        assert result.completeness_score == 1.0

    def test_basic_profile(self):
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        profiler = DataProfiler()
        result = profiler.profile(data)
        assert result.row_count == 2
        assert len(result.columns) == 2

    def test_numeric_detection(self):
        data = [{"val": 1}, {"val": 2}, {"val": 3}]
        profiler = DataProfiler()
        result = profiler.profile(data)
        col = result.columns[0]
        assert col.dtype == "numeric"
        assert col.mean is not None
        assert col.min_value == 1
        assert col.max_value == 3

    def test_string_detection(self):
        data = [{"s": "hello"}, {"s": "world"}]
        profiler = DataProfiler()
        result = profiler.profile(data)
        assert result.columns[0].dtype == "string"

    def test_boolean_detection(self):
        data = [{"flag": True}, {"flag": False}]
        profiler = DataProfiler()
        result = profiler.profile(data)
        assert result.columns[0].dtype == "boolean"

    def test_date_detection(self):
        data = [{"d": "2024-01-01"}, {"d": "2024-06-15"}]
        profiler = DataProfiler()
        result = profiler.profile(data)
        assert result.columns[0].dtype == "date"

    def test_null_handling(self):
        data = [{"val": 1}, {"val": None}, {"val": 3}]
        profiler = DataProfiler()
        result = profiler.profile(data)
        col = result.columns[0]
        assert col.null_count == 1
        assert abs(col.null_ratio - 1 / 3) < 0.01

    def test_completeness_score(self):
        data = [{"a": 1, "b": 2}, {"a": None, "b": None}]
        profiler = DataProfiler()
        result = profiler.profile(data)
        assert result.completeness_score == 0.5

    def test_cardinality(self):
        data = [{"x": "a"}, {"x": "a"}, {"x": "b"}]
        profiler = DataProfiler()
        result = profiler.profile(data)
        col = result.columns[0]
        assert col.unique_count == 2
        assert abs(col.cardinality_ratio - 2 / 3) < 0.01


class TestSchemaValidator:
    def test_valid_data(self):
        validator = SchemaValidator()
        data = [{"age": 25}, {"age": 30}]
        rules = [SchemaRule(column="age", expected_type="numeric", required=True)]
        result = validator.validate(data, rules)
        assert result.valid is True
        assert result.errors == []

    def test_missing_required_column(self):
        validator = SchemaValidator()
        data = [{"age": 25}, {"age": None}]
        rules = [SchemaRule(column="age", expected_type="numeric", required=True)]
        result = validator.validate(data, rules)
        assert result.valid is False
        assert "missing" in result.errors[0].lower()

    def test_wrong_type(self):
        validator = SchemaValidator()
        data = [{"age": "not a number"}]
        rules = [SchemaRule(column="age", expected_type="numeric")]
        result = validator.validate(data, rules)
        assert result.valid is False
        assert "wrong type" in result.errors[0].lower()

    def test_min_value_warning(self):
        validator = SchemaValidator()
        data = [{"score": -5}]
        rules = [SchemaRule(column="score", expected_type="numeric", min_value=0)]
        result = validator.validate(data, rules)
        assert result.valid is True
        assert len(result.warnings) > 0

    def test_max_value_warning(self):
        validator = SchemaValidator()
        data = [{"score": 150}]
        rules = [SchemaRule(column="score", expected_type="numeric", max_value=100)]
        result = validator.validate(data, rules)
        assert result.valid is True
        assert len(result.warnings) > 0

    def test_optional_column_with_nulls(self):
        validator = SchemaValidator()
        data = [{"x": None}]
        rules = [SchemaRule(column="x", expected_type="string", required=False)]
        result = validator.validate(data, rules)
        assert result.valid is True


class TestOutlierDetector:
    def test_no_outliers(self):
        detector = OutlierDetector()
        values = [10.0, 11.0, 12.0, 13.0, 14.0]
        result = detector.detect(values)
        assert result.outlier_count == 0

    def test_with_outliers(self):
        detector = OutlierDetector()
        values = [10.0, 11.0, 12.0, 13.0, 100.0]
        result = detector.detect(values)
        assert result.outlier_count >= 1
        assert 4 in result.outlier_indices

    def test_too_few_values(self):
        detector = OutlierDetector()
        result = detector.detect([1.0, 2.0])
        assert result.outlier_count == 0

    def test_custom_multiplier(self):
        detector = OutlierDetector()
        values = [10.0, 11.0, 12.0, 13.0, 20.0]
        strict = detector.detect(values, multiplier=0.5)
        lenient = detector.detect(values, multiplier=3.0)
        assert strict.outlier_count >= lenient.outlier_count

    def test_fences_computed(self):
        detector = OutlierDetector()
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = detector.detect(values)
        assert result.lower_fence <= min(values)
        assert result.upper_fence >= max(values)


class TestQualityEngine:
    def test_basic_assessment(self):
        engine = QualityEngine()
        data = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}, {"a": 3, "b": "z"}]
        report = engine.assess(data)
        assert isinstance(report, QualityReport)
        assert report.overall_score > 0

    def test_with_schema_rules(self):
        engine = QualityEngine()
        data = [{"age": 25}, {"age": 30}]
        rules = [SchemaRule(column="age", expected_type="numeric")]
        report = engine.assess(data, schema_rules=rules)
        assert report.validation.valid is True

    def test_recommendations_for_nulls(self):
        engine = QualityEngine()
        data = [{"x": None}, {"x": None}, {"x": 1}]
        report = engine.assess(data)
        assert any("null" in r.lower() for r in report.recommendations)

    def test_outlier_detection_in_report(self):
        engine = QualityEngine()
        data = [{"v": float(i)} for i in range(20)] + [{"v": 1000.0}]
        report = engine.assess(data)
        assert "v" in report.outlier_reports
        assert report.outlier_reports["v"].outlier_count >= 1

    def test_no_schema_rules(self):
        engine = QualityEngine()
        data = [{"a": 1}]
        report = engine.assess(data)
        assert report.validation.valid is True
