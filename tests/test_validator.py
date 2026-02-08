"""Tests for the validator module."""

from scrape_and_serve.validator import (
    ConfigValidator,
    DataValidator,
    ScrapedDataValidator,
    SelectorValidator,
    URLValidator,
)


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


class TestURLValidator:
    def test_valid_https_url(self):
        validator = URLValidator()
        result = validator.validate("https://example.com")
        assert result.is_valid
        assert result.errors == []

    def test_valid_http_url(self):
        validator = URLValidator()
        result = validator.validate("http://example.com/path")
        assert result.is_valid

    def test_invalid_empty_url(self):
        validator = URLValidator()
        result = validator.validate("")
        assert not result.is_valid
        assert any("required" in e.rule_type for e in result.errors)

    def test_invalid_url_with_spaces(self):
        validator = URLValidator()
        result = validator.validate("https://example .com")
        assert not result.is_valid

    def test_invalid_scheme(self):
        validator = URLValidator()
        result = validator.validate("ftp://example.com")
        assert not result.is_valid
        assert any("scheme" in e.rule_type for e in result.errors)

    def test_missing_domain(self):
        validator = URLValidator()
        result = validator.validate("https://")
        assert not result.is_valid


class TestSelectorValidator:
    def test_valid_selector(self):
        validator = SelectorValidator()
        result = validator.validate("div.class-name")
        assert result.is_valid
        assert result.errors == []

    def test_valid_complex_selector(self):
        validator = SelectorValidator()
        result = validator.validate("div > p.content[data-id='123']")
        assert result.is_valid

    def test_invalid_empty_selector(self):
        validator = SelectorValidator()
        result = validator.validate("")
        assert not result.is_valid

    def test_invalid_starts_with_combinator(self):
        validator = SelectorValidator()
        result = validator.validate("> div")
        assert not result.is_valid
        assert any("combinator" in e.message.lower() for e in result.errors)

    def test_invalid_unbalanced_brackets(self):
        validator = SelectorValidator()
        result = validator.validate("div[class='test'")
        assert not result.is_valid

    def test_invalid_unbalanced_parens(self):
        validator = SelectorValidator()
        result = validator.validate("div:nth-child(2")
        assert not result.is_valid


class TestConfigValidator:
    def test_valid_config(self):
        validator = ConfigValidator()
        config = {"url": "https://example.com", "selector": "div.content"}
        result = validator.validate(config)
        assert result.is_valid
        assert result.errors == []

    def test_missing_url(self):
        validator = ConfigValidator()
        config = {"selector": "div"}
        result = validator.validate(config)
        assert not result.is_valid
        assert any("url" in e.field for e in result.errors)

    def test_missing_selector(self):
        validator = ConfigValidator()
        config = {"url": "https://example.com"}
        result = validator.validate(config)
        assert not result.is_valid
        assert any("selector" in e.field for e in result.errors)

    def test_invalid_interval(self):
        validator = ConfigValidator()
        config = {"url": "https://example.com", "selector": "div", "interval_seconds": -10}
        result = validator.validate(config)
        assert not result.is_valid

    def test_low_interval_warning(self):
        validator = ConfigValidator()
        config = {"url": "https://example.com", "selector": "div", "interval_seconds": 30}
        result = validator.validate(config)
        assert result.is_valid
        assert len(result.warnings) > 0


class TestScrapedDataValidator:
    def test_valid_data(self):
        validator = ScrapedDataValidator()
        data = [{"title": "Item 1", "price": "$10"}, {"title": "Item 2", "price": "$20"}]
        schema = {"required_fields": ["title", "price"], "min_items": 1}
        result = validator.validate(data, schema)
        assert result.is_valid
        assert result.__dict__["completeness_score"] == 100.0

    def test_missing_fields(self):
        validator = ScrapedDataValidator()
        data = [{"title": "Item 1"}, {"price": "$20"}]
        schema = {"required_fields": ["title", "price"]}
        result = validator.validate(data, schema)
        assert result.is_valid  # Still valid, but with warnings
        assert len(result.warnings) > 0
        assert result.__dict__["completeness_score"] == 50.0

    def test_insufficient_items(self):
        validator = ScrapedDataValidator()
        data = [{"title": "Item 1"}]
        schema = {"required_fields": ["title"], "min_items": 5}
        result = validator.validate(data, schema)
        assert result.is_valid
        assert len(result.warnings) > 0

    def test_invalid_data_type(self):
        validator = ScrapedDataValidator()
        result = validator.validate("not a list", {"required_fields": []})
        assert not result.is_valid
