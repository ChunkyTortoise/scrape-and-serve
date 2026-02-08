"""Data validation rules: type checking, range validation, regex, custom rules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable


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
