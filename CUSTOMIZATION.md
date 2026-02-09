# Customization Guide

## Quick Start (5 minutes)

### Environment Setup
```bash
git clone https://github.com/ChunkyTortoise/scrape-and-serve.git
cd scrape-and-serve
pip install -r requirements.txt
make demo
```

No API keys or external services required. All scraping runs locally with BeautifulSoup4 and httpx.

### First Run Verification
```bash
make test  # Run all 136 tests
streamlit run app.py  # Launch UI at http://localhost:8501
```

Try the Excel converter with `demo_data/inventory.xlsx` or configure a scraper using the sample YAML format.

## Common Customizations

### 1. Branding & UI
**Streamlit Page Config** (`app.py`, line 1):
```python
st.set_page_config(
    page_title="Your Company Scraper",
    page_icon="🕷️",
    layout="wide"
)
```

**Tab Labels** (`app.py`, lines 22-60):
Modify tab names in the `st.tabs()` call to match your workflow (e.g., rename "Web Scraper" to "Competitor Monitor").

### 2. Scraper Configuration
**YAML Target Definition** (`demo_data/scrape_config.yaml`):
```yaml
targets:
  - name: "Product Monitor"
    url: "https://example.com/products"
    container_selector: ".product-card"
    fields:
      - name: "title"
        selector: ".product-title"
      - name: "price"
        selector: ".price"
        type: "float"
```

**Custom User Agents** (`scrape_and_serve/scraper.py`, line 35):
```python
headers = {
    "User-Agent": "YourCompany-Bot/1.0 (contact@yourcompany.com)"
}
result = scrape_html(url, headers=headers)
```

**Rate Limiting** (`scrape_and_serve/scheduler.py`, line 45):
```python
from asyncio import sleep

scheduler = Scheduler()
scheduler.schedule(target, interval_seconds=300, rate_limit_delay=2.0)
```

### 3. Price Monitoring
**Alert Thresholds** (`scrape_and_serve/price_monitor.py`, line 60):
```python
monitor = PriceHistory(
    alert_threshold_pct=5.0,  # Alert on 5% price change
    alert_callback=send_email_alert
)
monitor.track("Product SKU", price=99.99)
```

**Historical Export** (`price_monitor.py`, line 120):
```python
csv_data = export_history_csv(monitor)
with open("price_history.csv", "w") as f:
    f.write(csv_data)
```

### 4. Excel Converter
**Schema Detection** (`scrape_and_serve/excel_converter.py`, line 40):
Customize type inference by modifying `detect_schema()`:
- Date columns: Columns with "date" or "time" in name
- Numeric: Columns with numbers only
- Categorical: Columns with <10 unique values

**Generated App Customization** (`excel_converter.py`, line 180):
After generating Streamlit code, edit the output file to:
- Add filters and search
- Customize table styling
- Add computed columns

## Advanced Features

### Async Batch Scraping
**Concurrent Scraping** (`scrape_and_serve/scraper.py`, line 200):
```python
import asyncio
from scrape_and_serve.scraper import scrape_html_async

async def scrape_multiple(urls):
    tasks = [scrape_html_async(url) for url in urls]
    return await asyncio.gather(*tasks)

urls = ["https://site1.com", "https://site2.com"]
results = asyncio.run(scrape_multiple(urls))
```

### Scheduled Monitoring
**Cron-like Scheduling** (`scrape_and_serve/scheduler.py`):
```python
scheduler = Scheduler()

def on_price_change(result):
    if result.get("price_change_pct", 0) > 5:
        send_alert(result)

scheduler.schedule(
    target=my_scrape_target,
    interval_seconds=3600,  # Every hour
    callback=on_price_change
)
scheduler.start()
```

### Diff Visualization
**Track Page Changes** (`scrape_and_serve/diff_visualizer.py`):
```python
from scrape_and_serve.diff_visualizer import DiffTracker

tracker = DiffTracker()
tracker.snapshot("https://example.com/page", "Baseline")
# ... time passes ...
tracker.snapshot("https://example.com/page", "After Update")
diff = tracker.compare("Baseline", "After Update")
print(diff.unified_diff)  # Shows line-by-line changes
```

### SEO Content Generation
**Outline Generation** (`scrape_and_serve/seo_content.py`, line 90):
```python
from scrape_and_serve.seo_content import generate_outline

outline = generate_outline(
    topic="Real Estate AI",
    keywords=["property search", "AI assistant"],
    num_sections=5
)
```

**Content Scoring** (`seo_content.py`, line 140):
```python
from scrape_and_serve.seo_content import score_content

score = score_content(
    content="Your article text...",
    target_keywords=["AI", "automation"]
)
print(f"SEO Score: {score.total}/100")
print(f"Keyword Density: {score.keyword_density}%")
```

## Deployment

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501"]
```

```bash
docker build -t scrape-and-serve .
docker run -p 8501:8501 scrape-and-serve
```

### Streamlit Cloud
1. Push to GitHub
2. Connect at [share.streamlit.io](https://share.streamlit.io)
3. Point to `app.py`
4. No secrets required for basic scraping

### Scheduled Scraping (Production)
Use systemd or cron for background scraping:

```bash
# crontab entry for hourly scraping
0 * * * * cd /path/to/scrape-and-serve && python -m scrape_and_serve.cli scrape config.yaml
```

## Troubleshooting

### Common Errors

**Scraping Returns Empty Results**
- Verify CSS selectors: Inspect target page HTML with browser DevTools
- Check for JavaScript rendering: Use `playwright` for dynamic pages (see DEMO_MODE.md)
- Validate URL accessibility: Test with `curl -I <url>`

**Excel Converter Fails**
- Ensure file is valid .xlsx/.csv: `file inventory.xlsx` should show "Microsoft Excel"
- Check for merged cells or complex formatting: Simplify in Excel first
- Verify column headers exist: Converter expects first row to be headers

**Price Monitor Not Alerting**
- Check threshold: Default is 10% change, may be too high
- Verify callback function: Add print statements to `alert_callback`
- Ensure prices are numeric: Convert string prices to float

### Debug Mode
**Enable HTTP Logging** (`scraper.py`, line 1):
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now all httpx requests will be logged
```

**Scheduler Status** (`scheduler.py`, line 200):
```python
scheduler = Scheduler()
# ... schedule jobs ...
status = scheduler.get_status()
for job in status:
    print(f"{job.name}: {job.last_run} -> {job.next_run}")
```

## Support Resources

- **GitHub Issues**: [scrape-and-serve/issues](https://github.com/ChunkyTortoise/scrape-and-serve/issues)
- **Documentation**: Module docstrings in `scrape_and_serve/` directory
- **Live Demo**: [ct-scrape-and-serve.streamlit.app](https://ct-scrape-and-serve.streamlit.app)
- **Portfolio**: [chunkytortoise.github.io](https://chunkytortoise.github.io)
