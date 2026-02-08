"""Tests for the validators module (URL, scrape result, config validation)."""

import time

from scrape_and_serve.validators import validate_config, validate_scrape_result, validate_url


class TestValidateUrl:
    """Tests for validate_url()."""

    def test_valid_https(self):
        assert validate_url("https://example.com") is True

    def test_valid_http(self):
        assert validate_url("http://example.com/page") is True

    def test_valid_with_path_and_query(self):
        assert validate_url("https://example.com/path?q=1&b=2") is True

    def test_invalid_no_scheme(self):
        assert validate_url("example.com") is False

    def test_invalid_empty(self):
        assert validate_url("") is False

    def test_invalid_ftp_scheme(self):
        assert validate_url("ftp://files.example.com") is False

    def test_invalid_no_dot_in_netloc(self):
        assert validate_url("http://localhost") is False

    def test_invalid_with_spaces(self):
        assert validate_url("https://example .com/bad path") is False


class TestValidateScrapeResult:
    """Tests for validate_scrape_result()."""

    def test_valid_result(self):
        result = validate_scrape_result(
            {
                "url": "https://example.com",
                "content": "<html>hello</html>",
                "timestamp": time.time(),
            }
        )
        assert result.valid is True
        assert result.issues == []

    def test_missing_url(self):
        result = validate_scrape_result({"content": "hello", "timestamp": 123})
        assert result.valid is False
        assert any("url" in i.lower() for i in result.issues)

    def test_missing_content(self):
        result = validate_scrape_result({"url": "https://example.com", "timestamp": 123})
        assert result.valid is False
        assert any("content" in i.lower() for i in result.issues)

    def test_missing_timestamp(self):
        result = validate_scrape_result(
            {
                "url": "https://example.com",
                "content": "hello",
            }
        )
        assert result.valid is False
        assert any("timestamp" in i.lower() for i in result.issues)

    def test_empty_content_warns(self):
        result = validate_scrape_result(
            {
                "url": "https://example.com",
                "content": "",
                "timestamp": time.time(),
            }
        )
        assert result.valid is True  # valid but with warning
        assert any("empty" in w.lower() for w in result.warnings)

    def test_missing_status_code_warns(self):
        result = validate_scrape_result(
            {
                "url": "https://example.com",
                "content": "hello",
                "timestamp": time.time(),
            }
        )
        assert result.valid is True
        assert any("status_code" in w.lower() for w in result.warnings)

    def test_error_status_code_warns(self):
        result = validate_scrape_result(
            {
                "url": "https://example.com",
                "content": "error page",
                "timestamp": time.time(),
                "status_code": 404,
            }
        )
        assert result.valid is True
        assert any("404" in w for w in result.warnings)


class TestValidateConfig:
    """Tests for validate_config()."""

    def test_valid_config(self):
        result = validate_config({"url": "https://example.com"})
        assert result.valid is True

    def test_missing_url(self):
        result = validate_config({})
        assert result.valid is False
        assert any("url" in i.lower() for i in result.issues)

    def test_invalid_url(self):
        result = validate_config({"url": "not-a-url"})
        assert result.valid is False
        assert any("invalid url" in i.lower() for i in result.issues)

    def test_invalid_interval_negative(self):
        result = validate_config({"url": "https://example.com", "interval_seconds": -10})
        assert result.valid is False
        assert any("interval" in i.lower() for i in result.issues)

    def test_invalid_interval_zero(self):
        result = validate_config({"url": "https://example.com", "interval_seconds": 0})
        assert result.valid is False

    def test_low_interval_warns(self):
        result = validate_config({"url": "https://example.com", "interval_seconds": 30})
        assert result.valid is True
        assert any("rate limiting" in w.lower() for w in result.warnings)

    def test_invalid_enabled_type(self):
        result = validate_config({"url": "https://example.com", "enabled": "yes"})
        assert result.valid is False
        assert any("enabled" in i.lower() for i in result.issues)

    def test_full_valid_config(self):
        result = validate_config(
            {
                "url": "https://example.com",
                "interval_seconds": 3600,
                "name": "my-job",
                "enabled": True,
                "fields": ["title", "price"],
            }
        )
        assert result.valid is True
        assert result.issues == []
        assert result.warnings == []
