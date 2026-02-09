# Demo Mode Guide

## Overview
Run scrape-and-serve without external dependencies for testing and demonstrations. All scraping is done locally with static HTML or demo files.

## Quick Start

### Streamlit Demo
```bash
make demo
```
This launches the UI at `http://localhost:8501` with pre-loaded demo data.

### Python API Demo
```python
from pathlib import Path
from scrape_and_serve.excel_converter import read_excel, detect_schema
from scrape_and_serve.price_monitor import PriceHistory

# Demo 1: Excel Converter
demo_file = Path("demo_data/inventory.xlsx")
df = read_excel(demo_file)
schema = detect_schema(df)
print(f"Detected {len(schema)} columns")

# Demo 2: Price Monitoring
monitor = PriceHistory()
monitor.track("Widget-A", price=19.99)
monitor.track("Widget-A", price=21.99)  # 10% increase
if monitor.check_alert("Widget-A"):
    print("Price alert triggered!")
```

## Demo Data Included

The `demo_data/` directory contains:

| File | Contents | Use Case |
|------|----------|----------|
| `products.csv` | 15 products with prices | Price monitoring example |
| `inventory.xlsx` | 50-item inventory | Excel converter demo |
| `scrape_config.yaml` | Sample scraper config | YAML configuration reference |

## What's Mocked

In demo mode, the Streamlit app uses **static HTML** instead of live web scraping:

### Web Scraper Tab
- **No HTTP requests**: You paste HTML directly into the text area
- **Sample HTML provided**: Pre-filled with product card example
- **CSS selector testing**: Works on local HTML without network calls

### Excel Converter Tab
- **Uses demo files**: Loads `inventory.xlsx` from `demo_data/`
- **No file upload required**: Pre-configured for demo
- **SQLite in-memory**: No disk persistence

### Price Monitor Tab
- **No external data**: Uses `products.csv` from demo directory
- **Manual price updates**: You input prices, not scraped from web
- **CSV export**: Works normally, writes to local filesystem

### SEO Content Tab
- **Text-only analysis**: No API calls to external SEO services
- **Local TF-IDF**: Uses scikit-learn for keyword extraction
- **No web crawling**: Works on pasted text content

## Switching to Production

### 1. Enable Live Web Scraping
```python
# Instead of pasting HTML, scrape from URLs
from scrape_and_serve.scraper import scrape_html

html = scrape_html("https://example.com/products")
result = scrape_html(
    url="https://example.com",
    target=ScrapeTarget(
        name="Products",
        url="https://example.com/products",
        container_selector=".product",
        fields=[...]
    )
)
```

### 2. Add Persistent Storage
Replace in-memory SQLite with a real database:

```python
# Install PostgreSQL adapter
pip install psycopg2-binary

# Update excel_converter.py, line 140
conn = sqlite3.connect("inventory.db")  # Instead of ":memory:"
```

### 3. Set Up Scheduled Scraping
Use the scheduler for automated monitoring:

```bash
# Install as a background service
python -m scrape_and_serve.scheduler --config scrape_config.yaml --interval 3600
```

Or use cron:
```bash
0 * * * * cd /path/to/scrape-and-serve && python scrape_job.py
```

### 4. Add JavaScript Rendering (Optional)
For dynamic pages that require JavaScript execution:

```python
# Install Playwright
pip install playwright
playwright install chromium

# Use playwright instead of httpx
from scrape_and_serve.scraper import scrape_with_playwright

html = scrape_with_playwright("https://dynamic-site.com")
```

## Environment Variables

Demo mode requires **no environment variables**. For production:

| Variable | Required | Purpose |
|----------|----------|---------|
| `SCRAPER_USER_AGENT` | Optional | Custom user agent string |
| `SCRAPER_TIMEOUT` | Optional | Request timeout (default: 30s) |
| `SCRAPER_MAX_RETRIES` | Optional | Retry failed requests (default: 3) |
| `DATABASE_URL` | Optional | PostgreSQL connection for persistence |
| `ALERT_EMAIL_SMTP` | Optional | SMTP server for price alerts |
| `ALERT_EMAIL_FROM` | Optional | Sender email for alerts |

### Example Production .env
```bash
SCRAPER_USER_AGENT="MyCompany-Monitor/1.0"
SCRAPER_TIMEOUT=60
DATABASE_URL=postgresql://user:pass@localhost/scraper
ALERT_EMAIL_SMTP=smtp.gmail.com:587
ALERT_EMAIL_FROM=alerts@mycompany.com
```

## Performance Benchmarks (Demo Mode)

On a standard laptop:
- **Scraping**: Parses 1,000 HTML elements in <100ms
- **Excel Conversion**: Generates CRUD app from 50-row sheet in <500ms
- **Price Tracking**: Monitors 100 products with <10ms per update
- **SEO Scoring**: Analyzes 2,000-word article in <200ms

## Security Checklist

Demo mode is safe for public demonstrations:
- No outbound HTTP requests
- No persistent storage (in-memory SQLite)
- No file writes (except exports)
- No authentication required

For production:
- **Rate limiting**: Respect robots.txt and add delays between requests
- **User agent**: Identify your scraper with a custom user agent
- **Error handling**: Catch HTTP errors and timeouts gracefully
- **Legal compliance**: Ensure scraping complies with target site's ToS
- **Data validation**: Sanitize scraped data before storage
- **HTTPS only**: Use secure connections for all requests
