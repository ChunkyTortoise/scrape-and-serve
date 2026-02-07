"""Tests for price monitor module."""

from scrape_and_serve.price_monitor import (
    PriceHistory,
    export_history_csv,
    ingest_scrape_results,
)
from scrape_and_serve.scraper import ScrapeResult


class TestPriceHistory:
    def test_add_first_observation(self):
        h = PriceHistory()
        alert = h.add_observation("Widget", 10.0, "shop")
        assert alert is None
        assert len(h.records) == 1

    def test_no_alert_within_threshold(self):
        h = PriceHistory(alert_threshold_pct=10.0)
        h.add_observation("Widget", 100.0, "shop")
        alert = h.add_observation("Widget", 105.0, "shop")
        assert alert is None

    def test_alert_on_price_drop(self):
        h = PriceHistory(alert_threshold_pct=5.0)
        h.add_observation("Widget", 100.0, "shop")
        alert = h.add_observation("Widget", 90.0, "shop")
        assert alert is not None
        assert alert.alert_type == "drop"
        assert alert.change_pct == -10.0

    def test_alert_on_price_increase(self):
        h = PriceHistory(alert_threshold_pct=5.0)
        h.add_observation("Widget", 100.0, "shop")
        alert = h.add_observation("Widget", 120.0, "shop")
        assert alert is not None
        assert alert.alert_type == "increase"
        assert alert.change_pct == 20.0

    def test_get_products(self):
        h = PriceHistory()
        h.add_observation("A", 10, "s")
        h.add_observation("B", 20, "s")
        h.add_observation("A", 11, "s")
        assert h.get_products() == ["A", "B"]

    def test_latest_prices(self):
        h = PriceHistory()
        h.add_observation("Widget", 10, "s")
        h.add_observation("Widget", 15, "s")
        latest = h.latest_prices()
        assert latest["Widget"].price == 15

    def test_price_summary(self):
        h = PriceHistory()
        h.add_observation("Widget", 10, "s")
        h.add_observation("Widget", 20, "s")
        h.add_observation("Widget", 30, "s")
        summary = h.price_summary()
        assert len(summary) == 1
        assert summary[0]["min"] == 10
        assert summary[0]["max"] == 30
        assert summary[0]["avg"] == 20.0
        assert summary[0]["observations"] == 3

    def test_product_history(self):
        h = PriceHistory()
        h.add_observation("A", 10, "s")
        h.add_observation("B", 20, "s")
        h.add_observation("A", 15, "s")
        history = h.get_product_history("A")
        assert len(history) == 2
        assert history[0].price == 10
        assert history[1].price == 15


class TestIngestScrapeResults:
    def test_ingest(self):
        h = PriceHistory(alert_threshold_pct=5.0)
        result = ScrapeResult(
            target_name="shop",
            url="https://example.com",
            items=[
                {"name": "Widget", "price": "$100.00"},
                {"name": "Gadget", "price": "$50.00"},
            ],
        )
        alerts = ingest_scrape_results(h, result)
        assert len(alerts) == 0
        assert len(h.records) == 2

    def test_ingest_with_alert(self):
        h = PriceHistory(alert_threshold_pct=5.0)
        h.add_observation("Widget", 100.0, "shop")
        result = ScrapeResult(
            target_name="shop",
            url="https://example.com",
            items=[{"name": "Widget", "price": "$80.00"}],
        )
        alerts = ingest_scrape_results(h, result)
        assert len(alerts) == 1
        assert alerts[0].alert_type == "drop"

    def test_skip_missing_fields(self):
        h = PriceHistory()
        result = ScrapeResult(
            target_name="shop",
            url="https://example.com",
            items=[{"name": "", "price": "$10"}, {"name": "X", "price": ""}],
        )
        ingest_scrape_results(h, result)
        assert len(h.records) == 0


class TestExportCSV:
    def test_export(self):
        h = PriceHistory()
        h.add_observation("Widget", 10, "shop")
        h.add_observation("Gadget", 20, "shop")
        csv_text = export_history_csv(h)
        assert "Widget" in csv_text
        assert "Gadget" in csv_text
        lines = csv_text.strip().split("\n")
        assert len(lines) == 3  # header + 2 rows
