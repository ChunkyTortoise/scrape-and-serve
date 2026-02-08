# Scrape-and-Serve

[![CI](https://github.com/ChunkyTortoise/scrape-and-serve/actions/workflows/ci.yml/badge.svg)](https://github.com/ChunkyTortoise/scrape-and-serve/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-62_passing-brightgreen)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-F1C40F.svg)](LICENSE)
[![Live Demo](https://img.shields.io/badge/Live_Demo-Streamlit_Cloud-FF4B4B.svg?logo=streamlit&logoColor=white)](https://ct-scrape-and-serve.streamlit.app)

**[Live Demo](https://ct-scrape-and-serve.streamlit.app)** — try it without installing anything.

**Small businesses spend 5+ hours per week manually checking competitor prices, emailing Excel files for inventory updates, and publishing content with zero SEO data.** Each task requires a different tool, a different workflow, and manual effort that scales linearly with product count. Scrape-and-Serve cuts that to minutes -- YAML-configured scrapers, automated price alerts, one-click Excel-to-web-app conversion, and SEO scoring from 0-100, all in one Python toolkit with a Streamlit UI.

## What This Solves

- **Manual price tracking doesn't scale** -- YAML-configurable scrapers monitor competitor pages on schedule, detect changes via content hashing, and alert when prices shift beyond configurable thresholds
- **Excel files trap data** -- Upload any .xlsx file, auto-detect the schema, and generate a Streamlit CRUD app backed by SQLite with full create/read/update/delete operations
- **Content ships without SEO basics** -- SEO scoring engine grades content 0-100 on keyword density, readability (Flesch-Kincaid), heading structure, and meta completeness, then generates optimized outlines

## Architecture

```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   Web Scraper    │  │  Price Monitor   │  │ Excel Converter  │  │   SEO Content    │
│ YAML-configured  │  │ Historical track │  │ .xlsx → CRUD app │  │ Outlines + Score │
│ CSS selectors    │  │ Alert thresholds │  │ SQLite backend   │  │ Keyword analysis │
│ Change detection │  │ CSV export       │  │ Code generation  │  │ Readability      │
└────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
         └──────────────────────┴──────────────────────┴──────────────────────┘
                                    Streamlit UI
```

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

> **Try instantly**: [https://ct-scrape-and-serve.streamlit.app](https://ct-scrape-and-serve.streamlit.app) — no install required.

```bash
git clone https://github.com/ChunkyTortoise/scrape-and-serve.git
cd scrape-and-serve
pip install -r requirements.txt

# Demo mode -- sample data, no config needed
make demo

# Run the test suite
make test
```

## Modules

| Module | What It Does | Key Details |
|--------|-------------|-------------|
| `scraper.py` | YAML-configurable web scraping | BeautifulSoup + httpx, CSS selector targeting, content hashing for change detection, configurable request intervals |
| `price_monitor.py` | Competitor price tracking | Historical price charts (Plotly), configurable alert thresholds, CSV export, supports multiple products per competitor |
| `excel_converter.py` | Excel-to-web app modernization | Upload .xlsx, auto-detect column types and schema, generate Streamlit CRUD app with SQLite backend and data migration |
| `seo_content.py` | SEO content optimization | Keyword density analysis, Flesch-Kincaid readability grades, heading structure audit, content outlines, scoring 0-100 |

## Demo Data

Ships with ready-to-use demo data:
- `demo_data/products.csv` -- 15 products with prices and categories
- `demo_data/inventory.xlsx` -- 50-item inventory with SKU, pricing, stock levels
- `demo_data/scrape_config.yaml` -- sample YAML scraper configuration

## Tech Stack

| Layer | Technology |
|-------|-----------|
| UI | Streamlit, Plotly |
| Scraping | BeautifulSoup4, httpx |
| Data | Pandas, SQLite |
| Config | PyYAML |
| Testing | pytest (62 tests) |
| CI | GitHub Actions (Python 3.11, 3.12) |
| Linting | Ruff |

## Project Structure

```
scrape-and-serve/
├── app.py                          # Streamlit application
├── scrape_and_serve/
│   ├── scraper.py                  # YAML-configurable web scraper
│   ├── price_monitor.py            # Price tracking + alerts
│   ├── excel_converter.py          # .xlsx → Streamlit CRUD + SQLite
│   └── seo_content.py              # SEO scoring + content outlines
├── demo_data/
│   ├── products.csv                # 15 products with prices
│   ├── inventory.xlsx              # 50-item inventory
│   └── scrape_config.yaml          # Sample scraper config
├── tests/                          # One test file per module
├── .github/workflows/ci.yml        # CI pipeline
├── Makefile                        # demo, test, lint, setup
└── requirements.txt
```

## Testing

```bash
make test                                       # Full suite (62 tests)
python -m pytest tests/ -v                     # Verbose output
python -m pytest tests/test_scraper.py         # Single module
```

## Related Projects

- [EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub) -- Real estate AI platform with BI dashboards and CRM integration
- [jorge_real_estate_bots](https://github.com/ChunkyTortoise/jorge_real_estate_bots) -- Three-bot lead qualification system (Lead, Buyer, Seller)
- [insight-engine](https://github.com/ChunkyTortoise/insight-engine) -- Upload CSV/Excel, get instant dashboards, predictive models, and reports
- [docqa-engine](https://github.com/ChunkyTortoise/docqa-engine) -- RAG document Q&A with hybrid retrieval and prompt engineering lab
- [Revenue-Sprint](https://github.com/ChunkyTortoise/Revenue-Sprint) -- AI-powered freelance pipeline: job scanning, proposal generation, prompt injection testing
- [ai-orchestrator](https://github.com/ChunkyTortoise/ai-orchestrator) -- AgentForge: unified async LLM interface (Claude, Gemini, OpenAI, Perplexity)
- [Portfolio](https://chunkytortoise.github.io)

## License

MIT
