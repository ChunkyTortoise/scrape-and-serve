# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-02-09

### Added
- Content intelligence module: sentiment analysis, entity extraction, keyword extraction, content classification
- Data quality profiler: column profiling, null detection, outlier detection, schema validation
- Data pipeline: composable DataFrame transformations with stage timing and validation
- 66 new tests covering content intelligence, data quality, and data pipeline modules
- Docker and docker-compose support for containerized deployment
- Architecture Decision Records (ADRs) for key design choices
- Benchmarks for HTML parsing, content extraction, data quality scoring, and URL validation
- Governance files: CHANGELOG, SECURITY, CODE_OF_CONDUCT

### Changed
- Updated README with mermaid architecture diagram and key metrics
- Test count updated from 136 to 302

## [0.1.0] - 2026-01-15

### Added
- YAML-configurable web scraper with CSS selectors and SHA-256 change detection
- Price monitor with historical tracking, alert thresholds, and CSV export
- Excel converter: .xlsx/.csv/.tsv to SQLite with auto-generated Streamlit CRUD app
- SEO content scoring (0-100) across five dimensions with outline generation
- SEO analyzer with keyword suggestions and content comparison
- Diff visualizer for page snapshot tracking and unified diffs
- Asyncio-based scheduler with status tracking and callbacks
- Data validator with type checking, range, regex, and custom rules
- Streamlit dashboard with interactive demo
- CI pipeline with GitHub Actions (Python 3.11, 3.12)
- 136 tests across 8 modules
