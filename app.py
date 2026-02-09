"""Scrape-and-Serve: Web scraping framework + Excel-to-web converter."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from scrape_and_serve.excel_converter import (
    detect_schema,
    generate_streamlit_code,
    read_excel,
)
from scrape_and_serve.price_monitor import PriceHistory, export_history_csv
from scrape_and_serve.scraper import ScrapeTarget, scrape_html
from scrape_and_serve.seo_content import generate_outline, score_content

DEMO_DIR = Path(__file__).parent / "demo_data"


def render_scraper_tab() -> None:
    """Render the web scraper demo tab."""
    st.subheader("Web Scraper")
    st.info("Demo mode: paste HTML or use sample HTML to test scraping.")

    sample_html = """
    <div class="product-card">
        <span class="product-title">Wireless Mouse</span>
        <span class="product-price">$24.99</span>
    </div>
    <div class="product-card">
        <span class="product-title">USB-C Hub</span>
        <span class="product-price">$34.99</span>
    </div>
    <div class="product-card">
        <span class="product-title">Laptop Stand</span>
        <span class="product-price">$49.99</span>
    </div>
    """

    html_input = st.text_area("HTML to scrape:", value=sample_html.strip(), height=200)
    selector = st.text_input("CSS Selector:", value=".product-card")

    col1, col2 = st.columns(2)
    with col1:
        field_name = st.text_input("Field name:", value="name")
        field_sel = st.text_input("Field selector:", value=".product-title")
    with col2:
        field_name2 = st.text_input("Field name 2:", value="price")
        field_sel2 = st.text_input("Field selector 2:", value=".product-price")

    if st.button("Scrape"):
        target = ScrapeTarget(
            name="demo",
            url="https://demo.local",
            selector=selector,
            fields={field_name: field_sel, field_name2: field_sel2},
        )
        result = scrape_html(html_input, target)
        if result.items:
            st.success(f"Found {len(result.items)} items")
            st.dataframe(pd.DataFrame(result.items))
        else:
            st.warning("No items found. Check your selectors.")


def render_price_monitor_tab() -> None:
    """Render the price monitor demo tab."""
    st.subheader("Price Monitor")

    if "price_history" not in st.session_state:
        history = PriceHistory(alert_threshold_pct=5.0)
        # Load demo products
        demo_csv = DEMO_DIR / "products.csv"
        if demo_csv.exists():
            df = pd.read_csv(demo_csv)
            for _, row in df.iterrows():
                history.add_observation(row["name"], row["price"], row.get("source", "demo"))
        st.session_state.price_history = history

    history: PriceHistory = st.session_state.price_history

    summary = history.price_summary()
    if summary:
        st.dataframe(pd.DataFrame(summary), width="stretch")

        products = history.get_products()
        selected = st.selectbox("Product:", products)
        if selected:
            points = history.get_product_history(selected)
            chart_df = pd.DataFrame([{"date": p.observed_at, "price": p.price} for p in points])

            # Validate data to prevent infinite extent warnings
            chart_df["price"] = pd.to_numeric(chart_df["price"], errors="coerce")
            chart_df = chart_df.dropna(subset=["price"])
            chart_df = chart_df[chart_df["price"].between(-1e10, 1e10)]  # Remove infinite values

            if not chart_df.empty:
                st.line_chart(chart_df.set_index("date"))
            else:
                st.warning("No valid price data to display.")

        if st.button("Export CSV"):
            csv_data = export_history_csv(history)
            st.download_button("Download", csv_data, "price_history.csv", "text/csv")
    else:
        st.caption("No price data. Place products.csv in demo_data/.")


def render_excel_converter_tab() -> None:
    """Render the Excel-to-web converter tab."""
    st.subheader("Excel-to-Web Converter")

    source = st.radio("Source:", ["Demo Inventory", "Upload File"])

    if source == "Demo Inventory":
        demo_file = DEMO_DIR / "inventory.xlsx"
        if demo_file.exists():
            sheets = read_excel(demo_file)
        else:
            st.warning("Demo file not found. Run `python demo_data/generate_demo_data.py` first.")
            return
    else:
        uploaded = st.file_uploader("Upload Excel/CSV:", type=["xlsx", "xls", "csv"])
        if not uploaded:
            return
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded.name}") as tmp:
            tmp.write(uploaded.read())
            sheets = read_excel(tmp.name)

    for sheet_name, df in sheets.items():
        st.markdown(f"**Sheet: {sheet_name}** ({len(df)} rows)")
        schema = detect_schema(df, sheet_name)

        col1, col2 = st.columns([2, 1])
        with col1:
            st.dataframe(df.head(10), width="stretch")
        with col2:
            st.markdown("**Detected Schema:**")
            for col in schema.columns:
                nullable = " (nullable)" if col.nullable else ""
                st.text(f"  {col.name}: {col.dtype}{nullable}")

        if st.button(f"Generate App Code for {sheet_name}", key=f"gen_{sheet_name}"):
            code = generate_streamlit_code(schema)
            st.code(code, language="python")


def render_seo_tab() -> None:
    """Render the SEO content module tab."""
    st.subheader("SEO Content Tool")

    tab_outline, tab_score = st.tabs(["Generate Outline", "Score Content"])

    with tab_outline:
        topic = st.text_input("Topic:", placeholder="web scraping with Python")
        keywords = st.text_input("Keywords (comma-separated):", placeholder="web scraping, beautifulsoup, playwright")
        num_sections = st.slider("Sections:", 3, 8, 5)

        if st.button("Generate Outline") and topic:
            kw_list = [k.strip() for k in keywords.split(",") if k.strip()] or [topic]
            outline = generate_outline(topic, kw_list, num_sections)
            st.markdown(f"### {outline.title}")
            st.caption(f"Meta: {outline.meta_description}")
            for i, section in enumerate(outline.sections, 1):
                st.markdown(f"**{i}. {section['heading']}**")
                st.caption(section["notes"])

    with tab_score:
        title = st.text_input("Article Title:", key="seo_title")
        meta = st.text_input("Meta Description:", key="seo_meta")
        content = st.text_area("Content (markdown):", height=200, key="seo_content")
        kw_input = st.text_input("Target Keywords:", key="seo_kw", placeholder="keyword1, keyword2")

        if st.button("Score") and content:
            kw_list = [k.strip() for k in kw_input.split(",") if k.strip()]
            result = score_content(content, title, meta, kw_list)

            col1, col2, col3 = st.columns(3)
            col1.metric("SEO Score", f"{result.total_score}/100")
            col2.metric("Words", result.word_count)
            col3.metric("Readability", f"Grade {result.readability_grade}")

            if result.issues:
                st.warning("Issues: " + " | ".join(result.issues))
            if result.suggestions:
                st.info("Suggestions: " + " | ".join(result.suggestions))


def main() -> None:
    """Main Streamlit application."""
    st.set_page_config(page_title="Scrape-and-Serve", layout="wide")
    st.title("Scrape-and-Serve")
    st.caption("Web scraping framework + Excel-to-web converter + SEO tools")

    tab_scrape, tab_price, tab_excel, tab_seo = st.tabs(
        ["Web Scraper", "Price Monitor", "Excel Converter", "SEO Content"]
    )

    with tab_scrape:
        render_scraper_tab()

    with tab_price:
        render_price_monitor_tab()

    with tab_excel:
        render_excel_converter_tab()

    with tab_seo:
        render_seo_tab()


if __name__ == "__main__":
    main()
