"""Competitor price monitoring with historical tracking and alerts."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from scrape_and_serve.scraper import ScrapeResult, clean_price


@dataclass
class PricePoint:
    """A single price observation."""

    product_name: str
    price: float
    source: str
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PriceAlert:
    """Alert when price crosses a threshold."""

    product_name: str
    previous_price: float
    current_price: float
    change_pct: float
    alert_type: str  # "drop" or "increase"
    source: str


@dataclass
class PriceHistory:
    """Historical price tracker for multiple products."""

    records: list[PricePoint] = field(default_factory=list)
    alert_threshold_pct: float = 5.0

    def add_observation(self, product_name: str, price: float, source: str) -> PriceAlert | None:
        """Record a price and return an alert if threshold is crossed."""
        point = PricePoint(product_name=product_name, price=price, source=source)
        self.records.append(point)

        # Find the most recent previous observation for this product
        previous = [r for r in self.records[:-1] if r.product_name == product_name and r.source == source]
        if not previous:
            return None

        last = previous[-1]
        if last.price == 0:
            return None

        change_pct = ((price - last.price) / last.price) * 100

        if abs(change_pct) >= self.alert_threshold_pct:
            alert_type = "drop" if change_pct < 0 else "increase"
            return PriceAlert(
                product_name=product_name,
                previous_price=last.price,
                current_price=price,
                change_pct=round(change_pct, 2),
                alert_type=alert_type,
                source=source,
            )
        return None

    def get_product_history(self, product_name: str) -> list[PricePoint]:
        """Get all price observations for a product."""
        return [r for r in self.records if r.product_name == product_name]

    def get_products(self) -> list[str]:
        """Get unique product names."""
        return sorted({r.product_name for r in self.records})

    def latest_prices(self) -> dict[str, PricePoint]:
        """Get the latest price point for each product."""
        latest: dict[str, PricePoint] = {}
        for record in self.records:
            latest[record.product_name] = record
        return latest

    def price_summary(self) -> list[dict[str, Any]]:
        """Summary statistics per product."""
        products: dict[str, list[float]] = {}
        for r in self.records:
            products.setdefault(r.product_name, []).append(r.price)

        summaries = []
        for name, prices in sorted(products.items()):
            summaries.append(
                {
                    "product": name,
                    "current": prices[-1],
                    "min": min(prices),
                    "max": max(prices),
                    "avg": round(sum(prices) / len(prices), 2),
                    "observations": len(prices),
                }
            )
        return summaries


def ingest_scrape_results(
    history: PriceHistory,
    result: ScrapeResult,
    name_field: str = "name",
    price_field: str = "price",
) -> list[PriceAlert]:
    """Ingest a ScrapeResult into price history, returning any alerts."""
    alerts: list[PriceAlert] = []
    for item in result.items:
        product_name = item.get(name_field, "")
        raw_price = item.get(price_field, "")
        if not product_name or not raw_price:
            continue
        price = clean_price(str(raw_price))
        if price is None:
            continue
        alert = history.add_observation(product_name, price, result.target_name)
        if alert:
            alerts.append(alert)
    return alerts


def export_history_csv(history: PriceHistory) -> str:
    """Export price history as CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["product_name", "price", "source", "observed_at"])
    for r in history.records:
        writer.writerow([r.product_name, r.price, r.source, r.observed_at.isoformat()])
    return output.getvalue()
