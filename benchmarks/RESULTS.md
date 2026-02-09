# Scrape-and-Serve Benchmark Results

**Date**: 2026-02-09 03:33:31

| Operation | Iterations | P50 (ms) | P95 (ms) | P99 (ms) | Throughput |
|-----------|-----------|----------|----------|----------|------------|
| HTML Tag Parsing (100 tags) | 1,000 | 0.0146 | 0.0153 | 0.0188 | 67,195 ops/sec |
| URL Validation (504 URLs) | 1,000 | 0.3586 | 0.3708 | 0.4212 | 2,776 ops/sec |
| Content Extraction + Word Freq (200 tags) | 500 | 0.2356 | 0.2418 | 0.2891 | 4,219 ops/sec |
| Data Quality Scoring (200 records) | 500 | 0.0727 | 0.0743 | 0.0787 | 13,756 ops/sec |

> All benchmarks use synthetic/mock data. No external services required.
