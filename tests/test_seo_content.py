"""Tests for SEO content module."""

from scrape_and_serve.seo_content import (
    analyze_keyword,
    count_keyword,
    generate_outline,
    keyword_density,
    readability_score,
    score_content,
)


class TestCountKeyword:
    def test_basic(self):
        assert count_keyword("web scraping with Python", "web scraping") == 1

    def test_case_insensitive(self):
        assert count_keyword("Python is great. PYTHON rules.", "python") == 2

    def test_no_match(self):
        assert count_keyword("hello world", "python") == 0

    def test_multiple(self):
        assert count_keyword("seo seo seo", "seo") == 3


class TestKeywordDensity:
    def test_basic(self):
        text = "python is great python is fun"  # 6 words, python appears 2 times (1 word each)
        density = keyword_density(text, "python")
        assert 30 < density < 40  # ~33%

    def test_empty(self):
        assert keyword_density("", "python") == 0.0

    def test_multi_word(self):
        text = "web scraping is easy web scraping is fun"  # 8 words, "web scraping" 2x (2 words)
        density = keyword_density(text, "web scraping")
        assert density == 50.0


class TestAnalyzeKeyword:
    def test_full_analysis(self):
        text = "Web scraping is easy.\n\nMore content about web scraping here."
        result = analyze_keyword(text, "web scraping", "Guide to Web Scraping")
        assert result.count == 2
        assert result.in_title is True
        assert result.in_first_paragraph is True

    def test_not_in_title(self):
        result = analyze_keyword("web scraping content", "web scraping", "My Guide")
        assert result.in_title is False

    def test_not_in_first_paragraph(self):
        text = "Introduction here.\n\nWeb scraping comes later."
        result = analyze_keyword(text, "web scraping")
        assert result.in_first_paragraph is False


class TestGenerateOutline:
    def test_basic(self):
        outline = generate_outline("Web Scraping", ["web scraping", "beautifulsoup"])
        assert "Web Scraping" in outline.title
        assert len(outline.sections) == 5
        assert outline.estimated_word_count == 1500

    def test_custom_sections(self):
        outline = generate_outline("Python", ["python"], num_sections=3)
        assert len(outline.sections) == 3

    def test_meta_description(self):
        outline = generate_outline("Data", ["data", "analytics", "bi"])
        assert "data" in outline.meta_description.lower()


class TestReadabilityScore:
    def test_simple_text(self):
        text = "The cat sat on the mat. The dog ate the bone."
        score = readability_score(text)
        assert 0 <= score <= 20

    def test_complex_text(self):
        text = (
            "The implementation of sophisticated algorithmic optimization methodologies "
            "necessitates comprehensive understanding of computational complexity theory "
            "and distributed systems architecture."
        )
        score = readability_score(text)
        assert score > 5


class TestScoreContent:
    def test_good_content(self):
        text = (
            "## Introduction\n\n"
            "Web scraping is the process of extracting data from websites. "
            "This guide covers web scraping techniques, tools, and best practices. " * 50 + "\n\n"
            "## Getting Started\n\n"
            "To start web scraping you need Python and BeautifulSoup. " * 20 + "\n\n"
            "## Advanced Techniques\n\n"
            "Advanced web scraping requires handling JavaScript rendering. " * 20
        )
        result = score_content(
            text,
            title="Complete Guide to Web Scraping with Python",
            meta_description=(
                "Learn web scraping with Python. Covers BeautifulSoup, "
                "Playwright, and best practices for data extraction."
            ),
            keywords=["web scraping", "python"],
        )
        assert result.total_score >= 50
        assert result.word_count > 500
        assert result.heading_count >= 3

    def test_poor_content(self):
        result = score_content(
            "Short text.",
            title="X",
            meta_description="",
            keywords=["missing keyword"],
        )
        assert result.total_score < 40
        assert len(result.issues) > 0

    def test_keyword_scoring(self):
        text = "SEO optimization is key. " * 50
        result = score_content(text, "SEO Guide", "Learn SEO optimization tips.", ["seo"])
        kw = result.keyword_scores[0]
        assert kw.keyword == "seo"
        assert kw.count > 0
