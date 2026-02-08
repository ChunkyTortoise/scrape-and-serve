"""YAML-configurable web scraper with change detection and robots.txt compliance."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup


@dataclass
class ScrapeTarget:
    """A single target to scrape."""

    name: str
    url: str
    selector: str
    fields: dict[str, str] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class ScrapeResult:
    """Result of a single scrape run."""

    target_name: str
    url: str
    items: list[dict[str, Any]]
    scraped_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    content_hash: str = ""
    error: str | None = None


def parse_config(config: dict[str, Any]) -> list[ScrapeTarget]:
    """Parse a YAML-style config dict into ScrapeTarget objects."""
    targets = []
    for entry in config.get("targets", []):
        targets.append(
            ScrapeTarget(
                name=entry["name"],
                url=entry["url"],
                selector=entry["selector"],
                fields=entry.get("fields", {}),
                headers=entry.get("headers", {}),
            )
        )
    return targets


def extract_fields(element: BeautifulSoup, fields: dict[str, str]) -> dict[str, str]:
    """Extract named fields from an HTML element using CSS selectors."""
    result: dict[str, str] = {}
    for field_name, css_sel in fields.items():
        found = element.select_one(css_sel)
        if found:
            if field_name.endswith("_href") and found.get("href"):
                result[field_name] = found["href"]
            else:
                result[field_name] = found.get_text(strip=True)
        else:
            result[field_name] = ""
    return result


def scrape_html(html: str, target: ScrapeTarget) -> ScrapeResult:
    """Scrape items from raw HTML using target config."""
    soup = BeautifulSoup(html, "html.parser")
    elements = soup.select(target.selector)

    items: list[dict[str, Any]] = []
    for el in elements:
        if target.fields:
            item = extract_fields(el, target.fields)
        else:
            item = {"text": el.get_text(strip=True)}
        items.append(item)

    content_hash = hashlib.sha256(str(items).encode()).hexdigest()[:16]
    return ScrapeResult(
        target_name=target.name,
        url=target.url,
        items=items,
        content_hash=content_hash,
    )


class RobotsChecker:
    """Check robots.txt compliance before scraping a URL."""

    USER_AGENT = "ScrapeAndServe"

    def __init__(self) -> None:
        self._cache: dict[str, list[str]] = {}

    def _robots_url(self, url: str) -> str:
        """Derive the robots.txt URL from a target URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    def _parse_rules(self, robots_text: str) -> list[str]:
        """Parse Disallow rules for our user-agent (or *)."""
        disallowed: list[str] = []
        applies = False

        for line in robots_text.splitlines():
            line = line.strip()
            if line.startswith("#") or not line:
                continue

            if line.lower().startswith("user-agent:"):
                agent = line.split(":", 1)[1].strip().lower()
                applies = agent == "*" or self.USER_AGENT.lower() in agent
            elif applies and line.lower().startswith("disallow:"):
                path = line.split(":", 1)[1].strip()
                if path:
                    disallowed.append(path)

        return disallowed

    async def fetch_rules(self, url: str) -> list[str]:
        """Fetch and cache robots.txt rules for a given URL's domain."""
        robots_url = self._robots_url(url)
        if robots_url in self._cache:
            return self._cache[robots_url]

        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                resp = await client.get(robots_url)
                if resp.status_code == 200:
                    rules = self._parse_rules(resp.text)
                else:
                    rules = []  # No robots.txt = everything allowed
        except (httpx.HTTPError, httpx.TimeoutException):
            rules = []  # Network error = allow (fail open)

        self._cache[robots_url] = rules
        return rules

    async def is_allowed(self, url: str) -> bool:
        """Check if the given URL is allowed by robots.txt."""
        rules = await self.fetch_rules(url)
        parsed = urlparse(url)
        path = parsed.path or "/"

        for disallowed in rules:
            if disallowed == "/":
                return False
            if path.startswith(disallowed):
                return False
        return True

    def is_allowed_sync(self, path: str, rules: list[str]) -> bool:
        """Synchronous check against pre-fetched rules."""
        if not path:
            path = "/"
        for disallowed in rules:
            if disallowed == "/":
                return False
            if path.startswith(disallowed):
                return False
        return True


# Module-level shared instance for convenience
_default_robots_checker = RobotsChecker()


async def fetch_and_scrape(
    target: ScrapeTarget,
    respect_robots: bool = True,
) -> ScrapeResult:
    """Fetch a URL and scrape it according to the target config.

    Args:
        target: The scrape target configuration.
        respect_robots: If True, checks robots.txt before fetching. Defaults to True.
    """
    try:
        if respect_robots:
            allowed = await _default_robots_checker.is_allowed(target.url)
            if not allowed:
                return ScrapeResult(
                    target_name=target.name,
                    url=target.url,
                    items=[],
                    error=f"Blocked by robots.txt: {target.url}",
                )

        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            headers = {"User-Agent": "ScrapeAndServe/0.1", **target.headers}
            resp = await client.get(target.url, headers=headers)
            resp.raise_for_status()
            return scrape_html(resp.text, target)
    except Exception as exc:
        return ScrapeResult(
            target_name=target.name,
            url=target.url,
            items=[],
            error=str(exc),
        )


def detect_changes(previous: ScrapeResult, current: ScrapeResult) -> dict[str, Any]:
    """Compare two scrape results and detect changes."""
    if previous.content_hash == current.content_hash:
        return {"changed": False, "added": [], "removed": []}

    prev_set = {str(sorted(item.items())) for item in previous.items}
    curr_set = {str(sorted(item.items())) for item in current.items}

    added_keys = curr_set - prev_set
    removed_keys = prev_set - curr_set

    added = [item for item in current.items if str(sorted(item.items())) in added_keys]
    removed = [item for item in previous.items if str(sorted(item.items())) in removed_keys]

    return {"changed": True, "added": added, "removed": removed}


def clean_price(text: str) -> float | None:
    """Extract a numeric price from text like '$1,234.56'."""
    match = re.search(r"[\d,]+\.?\d*", text.replace(",", ""))
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None
