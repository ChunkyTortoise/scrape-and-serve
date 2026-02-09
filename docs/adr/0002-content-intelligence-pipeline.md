# ADR 0002: Content Intelligence Pipeline

## Status
Accepted

## Context
Raw HTML scraped from web pages needs classification and structured extraction before it is useful for downstream consumers. Without processing, users receive unstructured blobs of HTML that require manual inspection and interpretation.

## Decision
Implement a multi-stage content intelligence pipeline: content type detection (article, product page, listing, etc.), named entity extraction, keyword extraction, and readability scoring. Each stage is independent and can be enabled or disabled per scrape job. Results are stored as structured metadata alongside the raw content.

## Consequences
- **Positive**: Rich metadata per page enables powerful downstream filtering, search, and analysis. Independent stages allow selective processing based on use case. Structured output integrates cleanly with databases and APIs.
- **Negative**: Processing overhead of approximately 50ms per page adds up at scale. Pipeline stages may need domain-specific tuning for optimal accuracy. Additional dependencies for NLP processing increase deployment complexity.
