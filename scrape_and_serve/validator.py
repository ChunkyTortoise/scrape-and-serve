"""Data validation rules: type checking, range validation, regex, custom rules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.parse import urlparse


@dataclass
class ValidationRule:
    """A single validation rule."""

    field: str
    rule_type: str  # "required", "type", "range", "regex", "custom"
    params: dict[str, Any] = field(default_factory=dict)
    message: str = ""


@dataclass
class ValidationError:
    """A validation error."""

    field: str
    rule_type: str
    message: str
    value: Any = None


@dataclass
class ValidationResult:
    """Result of validating a data record."""

    is_valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)


class DataValidator:
    """Validate data records against configurable rules.

    Supports: required, type (str/int/float/bool), range (min/max),
    regex pattern matching, and custom callable validators.
    """

    def __init__(self, rules: list[ValidationRule] | None = None):
        self._rules: list[ValidationRule] = rules or []

    def add_rule(self, rule: ValidationRule) -> None:
        """Add a validation rule."""
        self._rules.append(rule)

    def add_required(self, field: str, message: str = "") -> None:
        """Shorthand: add a required field rule."""
        self.add_rule(ValidationRule(field=field, rule_type="required", message=message or f"{field} is required"))

    def add_type(self, field: str, expected_type: str, message: str = "") -> None:
        """Shorthand: add a type check rule."""
        self.add_rule(
            ValidationRule(
                field=field,
                rule_type="type",
                params={"type": expected_type},
                message=message or f"{field} must be {expected_type}",
            )
        )

    def add_range(
        self, field: str, min_val: float | None = None, max_val: float | None = None, message: str = ""
    ) -> None:
        """Shorthand: add a range check rule."""
        params: dict[str, Any] = {}
        if min_val is not None:
            params["min"] = min_val
        if max_val is not None:
            params["max"] = max_val
        self.add_rule(
            ValidationRule(field=field, rule_type="range", params=params, message=message or f"{field} out of range")
        )

    def add_regex(self, field: str, pattern: str, message: str = "") -> None:
        """Shorthand: add a regex validation rule."""
        self.add_rule(
            ValidationRule(
                field=field,
                rule_type="regex",
                params={"pattern": pattern},
                message=message or f"{field} does not match pattern",
            )
        )

    def add_custom(self, field: str, validator: Callable[[Any], bool], message: str = "") -> None:
        """Shorthand: add a custom validator function."""
        self.add_rule(
            ValidationRule(
                field=field,
                rule_type="custom",
                params={"validator": validator},
                message=message or f"{field} failed custom validation",
            )
        )

    def validate(self, record: dict[str, Any]) -> ValidationResult:
        """Validate a single record against all rules."""
        errors: list[ValidationError] = []

        for rule in self._rules:
            error = self._check_rule(rule, record)
            if error:
                errors.append(error)

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    def validate_many(self, records: list[dict[str, Any]]) -> list[ValidationResult]:
        """Validate multiple records."""
        return [self.validate(r) for r in records]

    def _check_rule(self, rule: ValidationRule, record: dict[str, Any]) -> ValidationError | None:
        """Check a single rule against a record."""
        value = record.get(rule.field)

        if rule.rule_type == "required":
            if value is None or (isinstance(value, str) and not value.strip()):
                return ValidationError(field=rule.field, rule_type="required", message=rule.message, value=value)

        elif rule.rule_type == "type":
            if value is not None:
                type_map: dict[str, type | tuple[type, ...]] = {
                    "str": str,
                    "int": int,
                    "float": (int, float),
                    "bool": bool,
                }
                expected = type_map.get(rule.params["type"])
                if expected and not isinstance(value, expected):
                    return ValidationError(field=rule.field, rule_type="type", message=rule.message, value=value)

        elif rule.rule_type == "range":
            if value is not None and isinstance(value, (int, float)):
                if "min" in rule.params and value < rule.params["min"]:
                    return ValidationError(field=rule.field, rule_type="range", message=rule.message, value=value)
                if "max" in rule.params and value > rule.params["max"]:
                    return ValidationError(field=rule.field, rule_type="range", message=rule.message, value=value)

        elif rule.rule_type == "regex":
            if value is not None and isinstance(value, str):
                if not re.match(rule.params["pattern"], value):
                    return ValidationError(field=rule.field, rule_type="regex", message=rule.message, value=value)

        elif rule.rule_type == "custom":
            if value is not None:
                validator = rule.params.get("validator")
                if validator and not validator(value):
                    return ValidationError(field=rule.field, rule_type="custom", message=rule.message, value=value)

        return None

    @classmethod
    def from_config(cls, config: list[dict[str, Any]]) -> DataValidator:
        """Create validator from a list of rule dicts (e.g., from YAML).

        Each dict should have: field, rule_type, and optionally params, message.
        """
        rules = []
        for item in config:
            rules.append(
                ValidationRule(
                    field=item["field"],
                    rule_type=item["rule_type"],
                    params=item.get("params", {}),
                    message=item.get("message", ""),
                )
            )
        return cls(rules)


class URLValidator:
    """Validate URL format, scheme, and reachability."""

    ALLOWED_SCHEMES = {"http", "https"}

    def validate(self, url: str) -> ValidationResult:
        """Validate a URL for format and scheme.

        Args:
            url: The URL to validate

        Returns:
            ValidationResult with validity and error details
        """
        errors: list[ValidationError] = []

        if not url or not isinstance(url, str):
            errors.append(ValidationError(field="url", rule_type="required", message="URL is required", value=url))
            return ValidationResult(is_valid=False, errors=errors)

        # Remove whitespace
        url = url.strip()

        # Check for spaces or control characters
        if re.search(r"[\s\x00-\x1f]", url):
            errors.append(
                ValidationError(
                    field="url",
                    rule_type="format",
                    message="URL contains invalid characters (spaces or control chars)",
                    value=url,
                )
            )

        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            errors.append(
                ValidationError(field="url", rule_type="format", message=f"Invalid URL format: {e}", value=url)
            )
            return ValidationResult(is_valid=False, errors=errors)

        # Check scheme
        if parsed.scheme not in self.ALLOWED_SCHEMES:
            errors.append(
                ValidationError(
                    field="url",
                    rule_type="scheme",
                    message=f"URL scheme must be http or https, got: {parsed.scheme}",
                    value=url,
                )
            )

        # Check netloc (domain)
        if not parsed.netloc:
            errors.append(ValidationError(field="url", rule_type="format", message="URL must have a domain", value=url))
        elif "." not in parsed.netloc:
            errors.append(
                ValidationError(
                    field="url",
                    rule_type="format",
                    message="URL domain must contain at least one dot (e.g., example.com)",
                    value=url,
                )
            )

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)


class SelectorValidator:
    """Validate CSS selector syntax."""

    def validate(self, selector: str) -> ValidationResult:
        """Validate CSS selector syntax.

        Args:
            selector: The CSS selector to validate

        Returns:
            ValidationResult with validity and error details
        """
        errors: list[ValidationError] = []

        if not selector or not isinstance(selector, str):
            errors.append(
                ValidationError(field="selector", rule_type="required", message="Selector is required", value=selector)
            )
            return ValidationResult(is_valid=False, errors=errors)

        selector = selector.strip()

        # Check for obviously invalid patterns
        if selector.startswith((",", ">", "+", "~")):
            errors.append(
                ValidationError(
                    field="selector",
                    rule_type="syntax",
                    message="Selector cannot start with combinator",
                    value=selector,
                )
            )

        # Check for unbalanced brackets
        if selector.count("[") != selector.count("]"):
            errors.append(
                ValidationError(
                    field="selector",
                    rule_type="syntax",
                    message="Unbalanced brackets in selector",
                    value=selector,
                )
            )

        if selector.count("(") != selector.count(")"):
            errors.append(
                ValidationError(
                    field="selector",
                    rule_type="syntax",
                    message="Unbalanced parentheses in selector",
                    value=selector,
                )
            )

        # Check for empty parts (e.g., "div,,p")
        if ",," in selector or selector.endswith(","):
            errors.append(
                ValidationError(
                    field="selector", rule_type="syntax", message="Selector has empty parts", value=selector
                )
            )

        # Check for consecutive combinators (e.g., "div > > p")
        combinators = [">", "+", "~"]
        for i in range(len(combinators)):
            for j in range(len(combinators)):
                pattern = f"{combinators[i]} {combinators[j]}"
                if pattern in selector:
                    errors.append(
                        ValidationError(
                            field="selector",
                            rule_type="syntax",
                            message="Consecutive combinators are invalid",
                            value=selector,
                        )
                    )
                    break

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)


class ConfigValidator:
    """Validate scrape configuration dicts before execution."""

    def __init__(self):
        self._url_validator = URLValidator()

    def validate(self, config: dict[str, Any]) -> ValidationResult:
        """Validate a scrape configuration dict.

        Required fields: url, selectors (or selector)
        Optional fields: name, interval_seconds, enabled, headers, fields

        Args:
            config: Configuration dictionary

        Returns:
            ValidationResult with validity and error details
        """
        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []

        if not isinstance(config, dict):
            return ValidationResult(
                is_valid=False,
                errors=[
                    ValidationError(
                        field="config", rule_type="type", message="Config must be a dictionary", value=config
                    )
                ],
            )

        # Required: url
        if "url" not in config:
            errors.append(
                ValidationError(field="url", rule_type="required", message="Config must have 'url' field", value=None)
            )
        else:
            url_result = self._url_validator.validate(config["url"])
            if not url_result.is_valid:
                errors.extend(url_result.errors)

        # Required: selectors or selector
        has_selector = "selector" in config or "selectors" in config
        if not has_selector:
            errors.append(
                ValidationError(
                    field="selector",
                    rule_type="required",
                    message="Config must have 'selector' or 'selectors' field",
                    value=None,
                )
            )

        # Optional: interval_seconds
        if "interval_seconds" in config:
            interval = config["interval_seconds"]
            if not isinstance(interval, int) or interval <= 0:
                errors.append(
                    ValidationError(
                        field="interval_seconds",
                        rule_type="type",
                        message="interval_seconds must be a positive integer",
                        value=interval,
                    )
                )
            elif interval < 60:
                warnings.append(
                    ValidationError(
                        field="interval_seconds",
                        rule_type="range",
                        message="interval_seconds below 60 may cause rate limiting",
                        value=interval,
                    )
                )

        # Optional: enabled
        if "enabled" in config:
            enabled = config["enabled"]
            if not isinstance(enabled, bool):
                errors.append(
                    ValidationError(
                        field="enabled", rule_type="type", message="enabled must be a boolean", value=enabled
                    )
                )

        # Optional: fields
        if "fields" in config:
            fields = config["fields"]
            if not isinstance(fields, dict):
                errors.append(
                    ValidationError(
                        field="fields", rule_type="type", message="fields must be a dictionary", value=fields
                    )
                )

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


class ScrapedDataValidator:
    """Validate scraped data quality."""

    def validate(self, data: list[dict[str, Any]], schema: dict[str, Any]) -> ValidationResult:
        """Validate scraped data against a schema.

        Args:
            data: List of scraped data dictionaries
            schema: Schema dict with 'required_fields' and optional 'min_items'

        Returns:
            ValidationResult with completeness_score and error details
        """
        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []

        if not isinstance(data, list):
            return ValidationResult(
                is_valid=False,
                errors=[
                    ValidationError(field="data", rule_type="type", message="Data must be a list", value=type(data))
                ],
            )

        if not isinstance(schema, dict):
            return ValidationResult(
                is_valid=False,
                errors=[
                    ValidationError(
                        field="schema", rule_type="type", message="Schema must be a dictionary", value=type(schema)
                    )
                ],
            )

        # Check minimum items
        min_items = schema.get("min_items", 0)
        if len(data) < min_items:
            warnings.append(
                ValidationError(
                    field="data",
                    rule_type="count",
                    message=f"Expected at least {min_items} items, got {len(data)}",
                    value=len(data),
                )
            )

        # Check required fields in each item
        required_fields = schema.get("required_fields", [])
        if required_fields:
            total_fields = len(data) * len(required_fields)
            present_fields = 0

            for i, item in enumerate(data):
                if not isinstance(item, dict):
                    errors.append(
                        ValidationError(
                            field=f"data[{i}]",
                            rule_type="type",
                            message=f"Item {i} must be a dictionary",
                            value=type(item),
                        )
                    )
                    continue

                for field in required_fields:
                    if field in item and item[field]:
                        present_fields += 1
                    else:
                        warnings.append(
                            ValidationError(
                                field=f"data[{i}].{field}",
                                rule_type="missing",
                                message=f"Missing or empty field '{field}' in item {i}",
                                value=None,
                            )
                        )

            # Calculate completeness score (0-100)
            completeness_score = (present_fields / total_fields * 100) if total_fields > 0 else 100.0
        else:
            completeness_score = 100.0

        result = ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)
        # Store completeness score as a custom attribute
        result.__dict__["completeness_score"] = round(completeness_score, 1)

        return result
