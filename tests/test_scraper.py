"""Tests for scraper module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scrape_and_serve.scraper import (
    RobotsChecker,
    ScrapeTarget,
    clean_price,
    detect_changes,
    extract_fields,
    fetch_and_scrape,
    parse_config,
    scrape_html,
)

SAMPLE_HTML = """
<div class="product">
    <span class="name">Widget A</span>
    <span class="price">$29.99</span>
    <a class="link" href="/widget-a">Details</a>
</div>
<div class="product">
    <span class="name">Widget B</span>
    <span class="price">$49.99</span>
    <a class="link" href="/widget-b">Details</a>
</div>
<div class="product">
    <span class="name">Widget C</span>
    <span class="price">$19.99</span>
    <a class="link" href="/widget-c">Details</a>
</div>
"""


def _make_target(**overrides):
    defaults = {
        "name": "test",
        "url": "https://example.com",
        "selector": ".product",
        "fields": {"name": ".name", "price": ".price"},
    }
    defaults.update(overrides)
    return ScrapeTarget(**defaults)


class TestParseConfig:
    def test_empty_config(self):
        targets = parse_config({})
        assert targets == []

    def test_single_target(self):
        config = {
            "targets": [{"name": "shop", "url": "https://shop.com", "selector": ".item", "fields": {"title": ".t"}}]
        }
        targets = parse_config(config)
        assert len(targets) == 1
        assert targets[0].name == "shop"
        assert targets[0].fields == {"title": ".t"}

    def test_multiple_targets(self):
        config = {
            "targets": [
                {"name": "a", "url": "https://a.com", "selector": ".x"},
                {"name": "b", "url": "https://b.com", "selector": ".y"},
            ]
        }
        targets = parse_config(config)
        assert len(targets) == 2


class TestExtractFields:
    def test_basic_fields(self):
        from bs4 import BeautifulSoup

        html = '<div><span class="name">Foo</span><span class="price">$10</span></div>'
        soup = BeautifulSoup(html, "html.parser")
        result = extract_fields(soup, {"name": ".name", "price": ".price"})
        assert result == {"name": "Foo", "price": "$10"}

    def test_missing_field(self):
        from bs4 import BeautifulSoup

        html = '<div><span class="name">Bar</span></div>'
        soup = BeautifulSoup(html, "html.parser")
        result = extract_fields(soup, {"name": ".name", "missing": ".nope"})
        assert result["name"] == "Bar"
        assert result["missing"] == ""

    def test_href_field(self):
        from bs4 import BeautifulSoup

        html = '<div><a class="link" href="/page">Click</a></div>'
        soup = BeautifulSoup(html, "html.parser")
        result = extract_fields(soup, {"link_href": ".link"})
        assert result["link_href"] == "/page"


class TestScrapeHtml:
    def test_scrape_items(self):
        target = _make_target()
        result = scrape_html(SAMPLE_HTML, target)
        assert len(result.items) == 3
        assert result.items[0]["name"] == "Widget A"
        assert result.items[0]["price"] == "$29.99"

    def test_scrape_no_fields(self):
        target = _make_target(fields={})
        result = scrape_html(SAMPLE_HTML, target)
        assert len(result.items) == 3
        assert "text" in result.items[0]

    def test_content_hash(self):
        target = _make_target()
        r1 = scrape_html(SAMPLE_HTML, target)
        r2 = scrape_html(SAMPLE_HTML, target)
        assert r1.content_hash == r2.content_hash
        assert len(r1.content_hash) == 16

    def test_empty_html(self):
        target = _make_target()
        result = scrape_html("<div>nothing</div>", target)
        assert result.items == []


class TestDetectChanges:
    def test_no_change(self):
        target = _make_target()
        r1 = scrape_html(SAMPLE_HTML, target)
        r2 = scrape_html(SAMPLE_HTML, target)
        changes = detect_changes(r1, r2)
        assert changes["changed"] is False

    def test_added_item(self):
        target = _make_target()
        r1 = scrape_html(SAMPLE_HTML, target)
        extra_html = (
            SAMPLE_HTML + '<div class="product"><span class="name">Widget D</span><span class="price">$99</span></div>'
        )
        r2 = scrape_html(extra_html, target)
        changes = detect_changes(r1, r2)
        assert changes["changed"] is True
        assert len(changes["added"]) == 1
        assert changes["added"][0]["name"] == "Widget D"

    def test_removed_item(self):
        target = _make_target()
        full = scrape_html(SAMPLE_HTML, target)
        partial_html = '<div class="product"><span class="name">Widget A</span><span class="price">$29.99</span></div>'
        partial = scrape_html(partial_html, target)
        changes = detect_changes(full, partial)
        assert changes["changed"] is True
        assert len(changes["removed"]) == 2


class TestCleanPrice:
    def test_basic(self):
        assert clean_price("$29.99") == 29.99

    def test_with_commas(self):
        assert clean_price("$1,234.56") == 1234.56

    def test_no_match(self):
        assert clean_price("free") is None

    def test_integer(self):
        assert clean_price("$100") == 100.0


class TestRobotsChecker:
    def test_parse_disallow_all(self):
        checker = RobotsChecker()
        robots_txt = "User-agent: *\nDisallow: /"
        rules = checker._parse_rules(robots_txt)
        assert "/" in rules

    def test_parse_disallow_path(self):
        checker = RobotsChecker()
        robots_txt = "User-agent: *\nDisallow: /admin\nDisallow: /private"
        rules = checker._parse_rules(robots_txt)
        assert "/admin" in rules
        assert "/private" in rules

    def test_parse_allow_all(self):
        checker = RobotsChecker()
        robots_txt = "User-agent: *\nDisallow:"
        rules = checker._parse_rules(robots_txt)
        assert rules == []

    def test_parse_specific_agent(self):
        checker = RobotsChecker()
        robots_txt = "User-agent: ScrapeAndServe\nDisallow: /secret\n\nUser-agent: *\nDisallow: /other"
        rules = checker._parse_rules(robots_txt)
        assert "/secret" in rules
        assert "/other" in rules

    def test_parse_ignores_comments(self):
        checker = RobotsChecker()
        robots_txt = "# comment\nUser-agent: *\n# another comment\nDisallow: /blocked"
        rules = checker._parse_rules(robots_txt)
        assert rules == ["/blocked"]

    def test_is_allowed_sync_root_blocked(self):
        checker = RobotsChecker()
        assert checker.is_allowed_sync("/page", ["/"]) is False

    def test_is_allowed_sync_path_blocked(self):
        checker = RobotsChecker()
        assert checker.is_allowed_sync("/admin/users", ["/admin"]) is False

    def test_is_allowed_sync_path_allowed(self):
        checker = RobotsChecker()
        assert checker.is_allowed_sync("/products", ["/admin"]) is True

    def test_is_allowed_sync_empty_rules(self):
        checker = RobotsChecker()
        assert checker.is_allowed_sync("/anything", []) is True

    def test_robots_url_derivation(self):
        checker = RobotsChecker()
        assert checker._robots_url("https://example.com/page") == "https://example.com/robots.txt"
        assert checker._robots_url("https://shop.io:8080/items") == "https://shop.io:8080/robots.txt"

    @pytest.mark.asyncio
    async def test_is_allowed_blocked_url(self):
        checker = RobotsChecker()
        robots_txt = "User-agent: *\nDisallow: /private"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = robots_txt

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await checker.is_allowed("https://example.com/private/data")
            assert result is False

    @pytest.mark.asyncio
    async def test_is_allowed_permitted_url(self):
        checker = RobotsChecker()
        robots_txt = "User-agent: *\nDisallow: /private"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = robots_txt

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await checker.is_allowed("https://example.com/products")
            assert result is True

    @pytest.mark.asyncio
    async def test_is_allowed_no_robots_txt(self):
        checker = RobotsChecker()
        mock_resp = MagicMock()
        mock_resp.status_code = 404

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await checker.is_allowed("https://example.com/anything")
            assert result is True

    @pytest.mark.asyncio
    async def test_caches_rules(self):
        checker = RobotsChecker()
        robots_txt = "User-agent: *\nDisallow: /blocked"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = robots_txt

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            await checker.is_allowed("https://example.com/page1")
            await checker.is_allowed("https://example.com/page2")
            # Only one HTTP call since the second is cached
            assert mock_client.get.await_count == 1


class TestFetchAndScrapeRobots:
    @pytest.mark.asyncio
    async def test_blocked_by_robots(self):
        target = _make_target(url="https://example.com/private/page")

        with patch(
            "scrape_and_serve.scraper._default_robots_checker.is_allowed",
            new_callable=AsyncMock,
            return_value=False,
        ):
            result = await fetch_and_scrape(target, respect_robots=True)
            assert result.error is not None
            assert "robots.txt" in result.error
            assert result.items == []

    @pytest.mark.asyncio
    async def test_robots_bypass(self):
        """respect_robots=False skips robots.txt check."""
        target = _make_target(url="https://example.com/private/page")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = SAMPLE_HTML
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await fetch_and_scrape(target, respect_robots=False)
            assert result.error is None
            assert len(result.items) == 3
