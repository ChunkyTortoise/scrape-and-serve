"""URL, scrape result, and config validation utilities."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse


@dataclass
class ValidationResult:
    """Result of a validation check."""

    valid: bool
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_url(url: str) -> bool:
    """Validate that a string is a well-formed HTTP(S) URL.

    Returns True if the URL has a valid scheme (http/https),
    a non-empty netloc, and uses only allowed characters.
    """
    if not url or not isinstance(url, str):
        return False

    try:
        parsed = urlparse(url)
    except Exception:
        return False

    if parsed.scheme not in ("http", "https"):
        return False

    if not parsed.netloc:
        return False

    # Must have at least one dot in the netloc (e.g., example.com)
    if "." not in parsed.netloc:
        return False

    # Reject URLs with spaces or control characters
    if re.search(r"[\s\x00-\x1f]", url):
        return False

    return True


def validate_scrape_result(result: dict) -> ValidationResult:
    """Validate a scrape result dictionary.

    Required fields: url, content, timestamp.
    Warns on empty content, missing status_code, or very large content.
    """
    issues: list[str] = []
    warnings: list[str] = []

    if not isinstance(result, dict):
        return ValidationResult(valid=False, issues=["Result must be a dictionary"])

    # Required fields
    if "url" not in result:
        issues.append("Missing required field: url")
    elif not validate_url(result["url"]):
        issues.append("Invalid URL in result")

    if "content" not in result:
        issues.append("Missing required field: content")
    elif not result["content"]:
        warnings.append("Content is empty")

    if "timestamp" not in result:
        issues.append("Missing required field: timestamp")

    # Optional warnings
    if "status_code" not in result:
        warnings.append("Missing status_code field")
    elif isinstance(result.get("status_code"), int) and result["status_code"] >= 400:
        warnings.append(f"HTTP error status: {result['status_code']}")

    content = result.get("content", "")
    if isinstance(content, str) and len(content) > 1_000_000:
        warnings.append("Content exceeds 1MB; consider truncating")

    return ValidationResult(valid=len(issues) == 0, issues=issues, warnings=warnings)


def validate_config(config: dict) -> ValidationResult:
    """Validate a scrape configuration dictionary.

    Required fields: url.
    Optional: interval_seconds (must be positive int), name, enabled, fields.
    """
    issues: list[str] = []
    warnings: list[str] = []

    if not isinstance(config, dict):
        return ValidationResult(valid=False, issues=["Config must be a dictionary"])

    # Required: url
    if "url" not in config:
        issues.append("Missing required field: url")
    elif not validate_url(config["url"]):
        issues.append("Invalid URL in config")

    # Optional: interval_seconds
    interval = config.get("interval_seconds")
    if interval is not None:
        if not isinstance(interval, int) or interval <= 0:
            issues.append("interval_seconds must be a positive integer")
        elif interval < 60:
            warnings.append("Interval under 60s may cause rate limiting")

    # Optional: name
    name = config.get("name")
    if name is not None and (not isinstance(name, str) or not name.strip()):
        warnings.append("Job name is empty or not a string")

    # Optional: enabled
    enabled = config.get("enabled")
    if enabled is not None and not isinstance(enabled, bool):
        issues.append("enabled must be a boolean")

    # Optional: fields
    fields = config.get("fields")
    if fields is not None:
        if not isinstance(fields, list):
            issues.append("fields must be a list")
        elif len(fields) == 0:
            warnings.append("fields list is empty")

    return ValidationResult(valid=len(issues) == 0, issues=issues, warnings=warnings)
