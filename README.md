# Scrape-and-Serve

[![CI](https://github.com/ChunkyTortoise/scrape-and-serve/actions/workflows/ci.yml/badge.svg)](https://github.com/ChunkyTortoise/scrape-and-serve/actions/workflows/ci.yml)

**YAML-configurable web scrapers, competitor price monitoring, Excel-to-Streamlit CRUD app generator, and SEO content tools.**

## Problem

Businesses track competitor prices in spreadsheets, manage inventory in Excel, and create content without SEO guidance. Each task requires a different tool. Scrape-and-Serve unifies web scraping, data modernization, and content optimization into one Python toolkit.

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

## Quick Start

```bash
pip install -r requirements.txt
make demo          # launches Streamlit app
make test          # runs all tests
```

## Modules

| Module | What It Does |
|--------|-------------|
| `scraper.py` | YAML-configurable web scraping with BeautifulSoup, change detection, content hashing |
| `price_monitor.py` | Competitor price tracking, alert thresholds, historical charts, CSV export |
| `excel_converter.py` | Upload .xlsx → auto-detect schema → generate Streamlit CRUD app + SQLite |
| `seo_content.py` | Keyword analysis, content outlines, SEO scoring (0-100), readability grades |

## Demo Data

Ships with ready-to-use demo data:
- `demo_data/products.csv` — 15 products with prices and categories
- `demo_data/inventory.xlsx` — 50-item inventory with SKU, pricing, stock levels
- `demo_data/scrape_config.yaml` — sample YAML scraper configuration

## Tech Stack

Python 3.11+ · BeautifulSoup4 · httpx · Pandas · Streamlit · Plotly · SQLite · PyYAML

## License

MIT
