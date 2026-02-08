"""Tests for the validator module."""

from scrape_and_serve.validator import DataValidator


class TestRequired:
    def test_missing_field(self):
        v = DataValidator()
        v.add_required("name")
        result = v.validate({})
        assert not result.is_valid
        assert result.errors[0].rule_type == "required"

    def test_empty_string(self):
        v = DataValidator()
        v.add_required("name")
        result = v.validate({"name": "   "})
        assert not result.is_valid
        assert result.errors[0].field == "name"

    def test_present_field(self):
        v = DataValidator()
        v.add_required("name")
        result = v.validate({"name": "Alice"})
        assert result.is_valid
        assert result.errors == []


class TestTypeCheck:
    def test_correct_type(self):
        v = DataValidator()
        v.add_type("age", "int")
        result = v.validate({"age": 25})
        assert result.is_valid

    def test_wrong_type(self):
        v = DataValidator()
        v.add_type("age", "int")
        result = v.validate({"age": "twenty-five"})
        assert not result.is_valid
        assert result.errors[0].rule_type == "type"

    def test_float_accepts_int(self):
        v = DataValidator()
        v.add_type("price", "float")
        result = v.validate({"price": 10})
        assert result.is_valid


class TestRange:
    def test_in_range(self):
        v = DataValidator()
        v.add_range("score", min_val=0, max_val=100)
        result = v.validate({"score": 50})
        assert result.is_valid

    def test_below_min(self):
        v = DataValidator()
        v.add_range("score", min_val=0, max_val=100)
        result = v.validate({"score": -5})
        assert not result.is_valid
        assert result.errors[0].rule_type == "range"

    def test_above_max(self):
        v = DataValidator()
        v.add_range("score", min_val=0, max_val=100)
        result = v.validate({"score": 150})
        assert not result.is_valid
        assert result.errors[0].rule_type == "range"


class TestRegex:
    def test_matching_pattern(self):
        v = DataValidator()
        v.add_regex("email", r"^[\w.+-]+@[\w-]+\.[\w.]+$")
        result = v.validate({"email": "user@example.com"})
        assert result.is_valid

    def test_non_matching(self):
        v = DataValidator()
        v.add_regex("email", r"^[\w.+-]+@[\w-]+\.[\w.]+$")
        result = v.validate({"email": "not-an-email"})
        assert not result.is_valid
        assert result.errors[0].rule_type == "regex"


class TestCustom:
    def test_passing_validator(self):
        v = DataValidator()
        v.add_custom("value", lambda x: x > 0, message="Must be positive")
        result = v.validate({"value": 10})
        assert result.is_valid

    def test_failing_validator(self):
        v = DataValidator()
        v.add_custom("value", lambda x: x > 0, message="Must be positive")
        result = v.validate({"value": -5})
        assert not result.is_valid
        assert result.errors[0].message == "Must be positive"


class TestValidateMany:
    def test_multiple_records(self):
        v = DataValidator()
        v.add_required("name")
        records = [{"name": "Alice"}, {"name": "Bob"}, {"name": "Charlie"}]
        results = v.validate_many(records)
        assert len(results) == 3
        assert all(r.is_valid for r in results)

    def test_mixed_results(self):
        v = DataValidator()
        v.add_required("name")
        records = [{"name": "Alice"}, {}, {"name": "Charlie"}]
        results = v.validate_many(records)
        assert len(results) == 3
        assert results[0].is_valid is True
        assert results[1].is_valid is False
        assert results[2].is_valid is True


class TestFromConfig:
    def test_config_loading(self):
        config = [
            {"field": "name", "rule_type": "required", "message": "Name needed"},
            {"field": "age", "rule_type": "type", "params": {"type": "int"}},
        ]
        v = DataValidator.from_config(config)
        result = v.validate({"name": "Alice", "age": 30})
        assert result.is_valid

    def test_config_with_params(self):
        config = [
            {"field": "score", "rule_type": "range", "params": {"min": 0, "max": 100}},
        ]
        v = DataValidator.from_config(config)
        result = v.validate({"score": 150})
        assert not result.is_valid
        assert result.errors[0].rule_type == "range"
