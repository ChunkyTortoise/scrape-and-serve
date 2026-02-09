# ADR 0003: Data Quality Validation

## Status
Accepted

## Context
Web scraping inherently produces inconsistent, incomplete, and sometimes inaccurate data. Pages change layout, return error pages, serve different content to bots, or contain stale information. Without quality validation, downstream consumers cannot distinguish reliable data from garbage.

## Decision
Implement multi-dimensional quality scoring across four axes: completeness (are all expected fields present), freshness (how recent is the content), consistency (does it match expected patterns), and accuracy (do values fall within reasonable ranges). Each dimension produces a 0-1 score, and a weighted composite score determines overall quality.

## Consequences
- **Positive**: Users can filter out low-quality data before it enters their systems. Quality trends are trackable over time, enabling detection of source degradation. Composite scoring provides a single quality metric for simple filtering.
- **Negative**: Quality heuristics can be domain-specific and may need per-source tuning. False quality scores (both positive and negative) are possible without domain context. The scoring system adds processing overhead to every scraped page.
