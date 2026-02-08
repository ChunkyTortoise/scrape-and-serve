# Scrape-and-Serve -- Benchmarks

Generated: 2026-02-08

## Test Suite Summary

136 tests across 8 modules. All tests run without network access or external dependencies.

| Module | Test File | Tests | Description |
|--------|-----------|-------|-------------|
| Scraper | `test_scraper.py` | ~18 | CSS selectors, change detection, async fetch |
| Price Monitor | `test_price_monitor.py` | ~18 | Alerts, history, summary stats, CSV export |
| Excel Converter | `test_excel_converter.py` | ~18 | Schema detection, SQLite creation, CRUD generation |
| SEO Content | `test_seo_content.py` | ~16 | Scoring, keyword density, readability, outlines |
| SEO Analyzer | `test_seo_analyzer.py` | ~16 | Keyword suggestions, content comparison, tech issues |
| Diff Visualizer | `test_diff_visualizer.py` | ~16 | Snapshots, diffs, history export, summaries |
| Scheduler | `test_scheduler.py` | ~16 | Job scheduling, status tracking, callbacks |
| Validator | `test_validator.py` | ~18 | Type checking, range, regex, custom rules |
| **Total** | **8 files** | **136** | |

## How to Reproduce

```bash
git clone https://github.com/ChunkyTortoise/scrape-and-serve.git
cd scrape-and-serve
pip install -r requirements.txt
make test
# or: python -m pytest tests/ -v
```

## Notes

- All scraper tests use mock HTTP responses (no network access)
- Excel converter tests create temporary SQLite databases
- SEO tests use sample content strings (no external APIs)
- Scheduler tests use simulated asyncio time
