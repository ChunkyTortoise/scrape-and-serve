# Scrape-and-Serve

[![CI](https://github.com/ChunkyTortoise/scrape-and-serve/actions/workflows/ci.yml/badge.svg)](https://github.com/ChunkyTortoise/scrape-and-serve/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-62_passing-brightgreen)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-F1C40F.svg)](LICENSE)
[![Live Demo](https://img.shields.io/badge/Live_Demo-Streamlit_Cloud-FF4B4B.svg?logo=streamlit&logoColor=white)](https://ct-scrape-and-serve.streamlit.app)

**[Live Demo](https://ct-scrape-and-serve.streamlit.app)** -- try it without installing anything.

**Teams spend 5+ hours per week manually checking competitor prices, reformatting spreadsheets for web access, and optimizing content for SEO** -- each task requiring a different tool, a different workflow, and manual effort that scales linearly with product count. Scrape-and-Serve consolidates all four into one Python toolkit: YAML-configured scrapers with change detection, automated price alerts with historical trends, one-command Excel-to-web-app conversion, and SEO scoring from 0-100 with actionable fixes.

## What This Solves

- **Manual price tracking does not scale** -- YAML-configurable scrapers monitor competitor pages on schedule, detect changes via SHA-256 content hashing, and alert when prices shift beyond configurable thresholds
- **Excel files trap data in inboxes** -- Upload any .xlsx file, auto-detect the schema (text, integer, float, date, boolean), and generate a Streamlit CRUD app backed by SQLite with full create/read/update/delete operations
- **Content ships without SEO basics** -- SEO scoring engine grades content 0-100 across five weighted dimensions (word count, meta description, title, keyword density, readability), then generates structured outlines with meta descriptions

## Architecture

```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   Web Scraper    │  │  Price Monitor   │  │ Excel Converter  │  │   SEO Content    │
│ YAML-configured  │  │ Historical track │  │ .xlsx -> CRUD app│  │ Outlines + Score │
│ CSS selectors    │  │ Alert thresholds │  │ SQLite backend   │  │ Keyword analysis │
│ Change detection │  │ CSV export       │  │ Code generation  │  │ Readability      │
└────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
         └──────────────────────┴──────────────────────┴──────────────────────┘
                                    Streamlit UI
```

## Modules

### Web Scraper (`scraper.py`)

YAML-configurable web scraper built on BeautifulSoup and httpx. Define targets declaratively -- each target specifies a URL, CSS selectors for item containers, and field-level sub-selectors for extracting structured data. The scraper supports custom request headers, async fetching with httpx (`follow_redirects=True`, 30s timeout), and automatic link extraction via `_href` field suffixes.

**Change detection** uses SHA-256 hashing of extracted items. The `detect_changes()` function compares previous and current scrape results, returning added and removed items with full diff detail. A `clean_price()` utility parses price strings (handling `$`, commas, decimals) into floats for downstream analysis.

Key capabilities:
- CSS selector targeting for item containers and individual fields
- Content hashing (SHA-256) for change detection between runs
- Diff tracking: identifies exactly which items were added or removed
- Async HTTP fetching with configurable headers and timeouts
- Automatic href extraction via `_href` field naming convention

### Price Monitor (`price_monitor.py`)

Competitor price tracking with configurable alert thresholds and historical trend analysis. The `PriceHistory` class maintains a time-series of `PricePoint` observations per product and source, firing `PriceAlert` events when percentage changes exceed the threshold (default: 5%).

The monitor integrates directly with the scraper module via `ingest_scrape_results()`, which extracts product names and prices from a `ScrapeResult` and records observations automatically. Summary statistics (current, min, max, average, observation count) are available per product via `price_summary()`.

Key capabilities:
- Configurable alert thresholds (e.g., fire on >5% price change)
- Historical price tracking with per-product, per-source granularity
- Summary statistics: current price, min, max, average, observation count
- CSV export of full price history via `export_history_csv()`
- Direct scraper integration via `ingest_scrape_results()`

### Excel Converter (`excel_converter.py`)

Upload any .xlsx (or .csv/.tsv) file and generate a fully functional Streamlit CRUD application backed by SQLite -- in one command. The converter auto-detects column types (text, integer, float, date, boolean) by inspecting pandas dtypes and attempting date parsing on ambiguous columns.

Schema detection produces a `TableSchema` with nullable flags and sample values per column. `create_sqlite_db()` creates the database with proper type mapping (TEXT, INTEGER, REAL) and auto-incrementing primary keys, then migrates all data. `generate_streamlit_code()` emits a complete, runnable Streamlit app with tabbed View/Add interfaces and type-appropriate input widgets (text inputs, number inputs, checkboxes, date pickers).

Key capabilities:
- Auto-detect column types: text, integer, float, date, boolean
- SQLite database creation with proper type mapping and NOT NULL constraints
- Auto-generated Streamlit CRUD app with tabbed View/Add interface
- Multi-sheet Excel support (each sheet parsed as a separate DataFrame)
- CSV and TSV file support alongside .xlsx
- SQL query interface via `query_db()` for custom read operations

### SEO Content (`seo_content.py`)

Content optimization engine that scores text 0-100 across five weighted dimensions and generates structured outlines for new articles. The `score_content()` function evaluates word count (0-20 pts), meta description quality (0-10 pts), title length (0-10 pts), keyword usage (0-30 pts across density, title presence, first-paragraph placement), heading structure (0-15 pts), and readability grade (0-15 pts).

Readability uses a simplified Flesch-Kincaid approximation based on average sentence length and average word length. Keyword analysis checks density (target: 0.5-3.0%), title inclusion, and first-paragraph placement. The engine returns actionable issues and suggestions alongside the numeric score.

Key capabilities:
- Composite SEO scoring from 0-100 with five weighted dimensions
- Keyword density analysis with optimal range detection (0.5-3.0%)
- Flesch-Kincaid readability grading (approximate grade level)
- Content outline generation with meta descriptions and section structure
- Actionable issues and suggestions for each scoring dimension
- Heading structure audit (H1-H6 detection and counting)

## Before / After

| Task | Before | After |
|------|--------|-------|
| **Competitor monitoring** | Manually visiting 15+ competitor websites daily, copy-pasting prices into spreadsheets | One YAML config defines all targets -- automated scrapes with content hashing detect changes and fire alerts |
| **Price tracking** | Stale spreadsheet logs, no historical trends, price drops discovered days late | Historical price charts (Plotly), configurable threshold alerts (e.g., >5% change), CSV export for reporting |
| **Inventory management** | Emailing .xlsx files between team members, no web access, version conflicts | Upload any .xlsx -- auto-detect schema, generate a live Streamlit CRUD app backed by SQLite in seconds |
| **Content optimization** | Publishing blog posts with zero keyword data, guessing at readability | SEO engine scores content 0-100 on keyword density, Flesch-Kincaid readability, heading structure, and meta tags |

## Typical Workflow

```
1. Define scrape targets         Write a YAML config with URLs, CSS selectors, and request intervals
                                 (see demo_data/scrape_config.yaml for a working example)

2. Run the scraper               $ python -m scrape_and_serve.scraper --config scrape_config.yaml
                                 Content hashing detects page changes automatically between runs

3. Set up price monitoring       Configure products + alert thresholds (e.g., notify on >5% price swing)
                                 Historical data accumulates across runs for trend analysis

4. Modernize an Excel file       Upload any .xlsx via the Streamlit UI -- columns auto-detected,
                                 SQLite database created, full CRUD app generated with zero code

5. Score your content            Paste or upload content into the SEO module -- get a 0-100 score
                                 with specific fixes for keyword density, readability, and structure

6. Review in Streamlit           All modules feed into one dashboard: scrape results, price charts,
                                 inventory CRUD, and SEO reports in a single browser tab
```

## Quick Start

> **Try instantly**: [https://ct-scrape-and-serve.streamlit.app](https://ct-scrape-and-serve.streamlit.app) -- no install required.

```bash
git clone https://github.com/ChunkyTortoise/scrape-and-serve.git
cd scrape-and-serve
pip install -r requirements.txt

# Demo mode -- sample data, no config needed
make demo

# Run the test suite
make test
```

## Demo Data

Ships with ready-to-use demo data for immediate exploration:

| File | Contents | Use Case |
|------|----------|----------|
| `demo_data/products.csv` | 15 products with prices and categories | Price monitoring, scraper output format |
| `demo_data/inventory.xlsx` | 50-item inventory with SKU, pricing, stock levels | Excel converter demo, CRUD app generation |
| `demo_data/scrape_config.yaml` | Sample YAML scraper configuration | Scraper target definition reference |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Scraping | BeautifulSoup4, httpx (async) |
| Data | Pandas, SQLite |
| UI | Streamlit, Plotly |
| Config | PyYAML |
| Testing | pytest (62 tests) |
| CI | GitHub Actions (Python 3.11, 3.12) |
| Linting | Ruff |

## Project Structure

```
scrape-and-serve/
├── app.py                          # Streamlit application entry point
├── scrape_and_serve/
│   ├── __init__.py
│   ├── scraper.py                  # YAML-configurable web scraper + change detection
│   ├── price_monitor.py            # Price tracking, alerts, CSV export
│   ├── excel_converter.py          # .xlsx -> SQLite + Streamlit CRUD generation
│   └── seo_content.py              # SEO scoring 0-100, outline generation
├── demo_data/
│   ├── generate_demo_data.py       # Reproducible sample data generator
│   ├── products.csv                # 15 products with prices
│   ├── inventory.xlsx              # 50-item inventory
│   └── scrape_config.yaml          # Sample scraper config
├── tests/
│   ├── test_scraper.py             # Scraper + change detection tests
│   ├── test_price_monitor.py       # Price tracking + alert tests
│   ├── test_excel_converter.py     # Schema detection + CRUD generation tests
│   └── test_seo_content.py         # SEO scoring + outline tests
├── .github/workflows/ci.yml        # CI pipeline (lint + test on 3.11/3.12)
├── .streamlit/config.toml          # Streamlit theme configuration
├── Makefile                        # demo, test, lint, clean, setup, generate-data
├── pyproject.toml                  # Ruff configuration
├── requirements.txt                # Production dependencies
└── requirements-dev.txt            # Development dependencies (pytest, ruff)
```

## Testing

62 tests across 4 test files, one per module. All tests run without network access or external dependencies.

```bash
make test                                       # Full suite (62 tests)
python -m pytest tests/ -v                      # Verbose output
python -m pytest tests/test_scraper.py          # Single module
python -m pytest tests/test_price_monitor.py    # Price tracking tests
python -m pytest tests/test_seo_content.py -k score  # Run specific tests by name
```

## Deploy

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/chunkytortoise/scrape-and-serve/main/app.py)

## Related Projects

- [EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub) -- Real estate AI platform with BI dashboards and CRM integration
- [jorge_real_estate_bots](https://github.com/ChunkyTortoise/jorge_real_estate_bots) -- Three-bot lead qualification system (Lead, Buyer, Seller)
- [Revenue-Sprint](https://github.com/ChunkyTortoise/Revenue-Sprint) -- AI-powered freelance pipeline: job scanning, proposal generation, prompt injection testing
- [ai-orchestrator](https://github.com/ChunkyTortoise/ai-orchestrator) -- AgentForge: unified async LLM interface (Claude, Gemini, OpenAI, Perplexity)
- [insight-engine](https://github.com/ChunkyTortoise/insight-engine) -- Upload CSV/Excel, get instant dashboards, predictive models, and reports
- [docqa-engine](https://github.com/ChunkyTortoise/docqa-engine) -- RAG document Q&A with hybrid retrieval and prompt engineering lab
- [Portfolio](https://chunkytortoise.github.io) -- Project showcase and services

## License

MIT -- see [LICENSE](LICENSE) for details.
