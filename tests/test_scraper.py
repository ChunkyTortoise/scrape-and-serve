"""Tests for scraper module."""

from scrape_and_serve.scraper import (
    ScrapeTarget,
    clean_price,
    detect_changes,
    extract_fields,
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
            "targets": [
                {"name": "shop", "url": "https://shop.com", "selector": ".item", "fields": {"title": ".t"}}
            ]
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
            SAMPLE_HTML
            + '<div class="product"><span class="name">Widget D</span>'
            '<span class="price">$99</span></div>'
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
