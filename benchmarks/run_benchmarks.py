"""Scrape-and-Serve Performance Benchmarks."""
import time
import random
import re
from pathlib import Path

random.seed(42)


def percentile(data, p):
    k = (len(data) - 1) * p / 100
    f = int(k)
    c = f + 1 if f + 1 < len(data) else f
    return data[f] + (k - f) * (data[c] - data[f])


# --- Synthetic data generators ---

def _generate_mock_html(tag_count=50):
    """Generate a mock HTML document with nested tags."""
    tags = ["div", "p", "span", "a", "h1", "h2", "h3", "ul", "li", "table", "tr", "td"]
    parts = ["<html><head><title>Test Page</title></head><body>"]
    for i in range(tag_count):
        tag = random.choice(tags)
        attrs = ""
        if tag == "a":
            attrs = f' href="https://example.com/page{i}"'
        elif tag == "div":
            attrs = f' class="section-{i % 5}"'
        parts.append(f"<{tag}{attrs}>Content block {i} with some text</{tag}>")
    parts.append("</body></html>")
    return "".join(parts)


MOCK_URLS = [
    f"https://example.com/page/{random.randint(1, 9999)}" for _ in range(500)
] + [
    f"ftp://bad.{random.randint(0,99)}.com",
    "not-a-url",
    "http://",
    "",
    "https://valid.example.org/path?q=1&r=2#frag",
]


# --- Benchmarks ---

def benchmark_html_tag_parsing():
    """HTML tag extraction via regex."""
    html = _generate_mock_html(100)
    tag_re = re.compile(r"<(\w+)[^>]*>")
    times = []
    for _ in range(1000):
        start = time.perf_counter()
        tags_found = tag_re.findall(html)
        tag_counts = {}
        for t in tags_found:
            tag_counts[t] = tag_counts.get(t, 0) + 1
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    times.sort()
    return {
        "op": "HTML Tag Parsing (100 tags)",
        "n": 1000,
        "p50": round(percentile(times, 50), 4),
        "p95": round(percentile(times, 95), 4),
        "p99": round(percentile(times, 99), 4),
        "ops_sec": round(1000 / (sum(times) / 1000), 1),
    }


def benchmark_url_validation():
    """URL validation with regex."""
    url_re = re.compile(
        r"^https?://"
        r"[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
        r"(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*"
        r"(:\d{1,5})?"
        r"(/[^\s]*)?$"
    )
    times = []
    for _ in range(1000):
        start = time.perf_counter()
        valid = [u for u in MOCK_URLS if url_re.match(u)]
        invalid = [u for u in MOCK_URLS if not url_re.match(u)]
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    times.sort()
    return {
        "op": "URL Validation (504 URLs)",
        "n": 1000,
        "p50": round(percentile(times, 50), 4),
        "p95": round(percentile(times, 95), 4),
        "p99": round(percentile(times, 99), 4),
        "ops_sec": round(1000 / (sum(times) / 1000), 1),
    }


def benchmark_content_extraction():
    """Content extraction: strip tags and normalize whitespace."""
    html = _generate_mock_html(200)
    strip_re = re.compile(r"<[^>]+>")
    ws_re = re.compile(r"\s+")
    times = []
    for _ in range(500):
        start = time.perf_counter()
        text = strip_re.sub(" ", html)
        text = ws_re.sub(" ", text).strip()
        words = text.split()
        word_freq = {}
        for w in words:
            wl = w.lower()
            word_freq[wl] = word_freq.get(wl, 0) + 1
        top_words = sorted(word_freq.items(), key=lambda x: -x[1])[:20]
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    times.sort()
    return {
        "op": "Content Extraction + Word Freq (200 tags)",
        "n": 500,
        "p50": round(percentile(times, 50), 4),
        "p95": round(percentile(times, 95), 4),
        "p99": round(percentile(times, 99), 4),
        "ops_sec": round(500 / (sum(times) / 1000), 1),
    }


def benchmark_data_quality_scoring():
    """Data quality scoring: completeness, freshness, consistency."""
    records = []
    for i in range(200):
        records.append({
            "url": f"https://example.com/{i}" if random.random() > 0.1 else None,
            "title": f"Title {i}" if random.random() > 0.05 else "",
            "body": f"Body text content {i} " * random.randint(1, 20) if random.random() > 0.15 else "",
            "scraped_at": time.time() - random.randint(0, 86400 * 30),
            "status_code": random.choice([200, 200, 200, 301, 404, 500]),
        })
    times = []
    now = time.time()
    for _ in range(500):
        start = time.perf_counter()
        scores = []
        for rec in records:
            completeness = sum([
                1 if rec["url"] else 0,
                1 if rec["title"] else 0,
                1 if rec["body"] else 0,
            ]) / 3.0
            age_days = (now - rec["scraped_at"]) / 86400
            freshness = max(0, 1.0 - age_days / 30)
            consistency = 1.0 if rec["status_code"] == 200 else 0.3
            quality = 0.4 * completeness + 0.3 * freshness + 0.3 * consistency
            scores.append(round(quality, 3))
        avg_quality = sum(scores) / len(scores)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    times.sort()
    return {
        "op": "Data Quality Scoring (200 records)",
        "n": 500,
        "p50": round(percentile(times, 50), 4),
        "p95": round(percentile(times, 95), 4),
        "p99": round(percentile(times, 99), 4),
        "ops_sec": round(500 / (sum(times) / 1000), 1),
    }


def main():
    results = []
    benchmarks = [
        benchmark_html_tag_parsing,
        benchmark_url_validation,
        benchmark_content_extraction,
        benchmark_data_quality_scoring,
    ]
    for bench in benchmarks:
        print(f"Running {bench.__doc__.strip()}...")
        r = bench()
        results.append(r)
        print(f"  P50: {r['p50']}ms | P95: {r['p95']}ms | P99: {r['p99']}ms | {r['ops_sec']} ops/sec")

    out = Path(__file__).parent / "RESULTS.md"
    with open(out, "w") as f:
        f.write("# Scrape-and-Serve Benchmark Results\n\n")
        f.write(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("| Operation | Iterations | P50 (ms) | P95 (ms) | P99 (ms) | Throughput |\n")
        f.write("|-----------|-----------|----------|----------|----------|------------|\n")
        for r in results:
            f.write(f"| {r['op']} | {r['n']:,} | {r['p50']} | {r['p95']} | {r['p99']} | {r['ops_sec']:,.0f} ops/sec |\n")
        f.write("\n> All benchmarks use synthetic/mock data. No external services required.\n")
    print(f"\nResults: {out}")


if __name__ == "__main__":
    main()
