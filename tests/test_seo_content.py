"""Tests for SEO content module."""

from scrape_and_serve.seo_content import (
    _average_sentence_length,
    _average_word_length,
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


class TestReadabilityEdgeCases:
    """Edge cases for readability scoring and internal helpers."""

    def test_empty_text_returns_zero(self):
        assert readability_score("") == 0.0

    def test_single_word(self):
        score = readability_score("Hello")
        assert score >= 0.0

    def test_very_long_sentences_high_grade(self):
        text = "This is a " + "very " * 30 + "long sentence."
        score = readability_score(text)
        assert score > 5  # long sentence => higher grade level

    def test_average_sentence_length_empty(self):
        assert _average_sentence_length("") == 0.0

    def test_average_word_length_empty(self):
        assert _average_word_length("") == 0.0


class TestKeywordEdgeCases:
    """Edge cases for keyword counting and density."""

    def test_keyword_density_no_match(self):
        assert keyword_density("hello world foo bar", "python") == 0.0

    def test_count_keyword_special_regex_chars(self):
        # Keyword contains regex special chars like "C++"
        text = "I love C++ and C++ is great"
        assert count_keyword(text, "C++") == 2

    def test_analyze_keyword_empty_title(self):
        result = analyze_keyword("web scraping data", "web scraping")
        assert result.in_title is False


class TestScoreContentEdgeCases:
    """Edge cases for meta description, title, and heading scoring."""

    def test_meta_description_too_short(self):
        result = score_content(
            "Some content " * 100,
            title="A Good Title That Is Thirty Plus Chars",
            meta_description="Short",
            keywords=["content"],
        )
        assert not result.has_meta_description
        assert any("meta description" in i.lower() for i in result.issues)

    def test_meta_description_too_long(self):
        long_meta = "A" * 200
        result = score_content(
            "Some content " * 100,
            title="A Good Title That Is Thirty Plus Chars",
            meta_description=long_meta,
            keywords=["content"],
        )
        assert not result.has_meta_description

    def test_title_too_short_triggers_suggestion(self):
        result = score_content(
            "Some words " * 100,
            title="Hi",
            meta_description="A reasonable meta description for the page content here.",
            keywords=["words"],
        )
        assert any("title" in s.lower() for s in result.suggestions)

    def test_title_too_long_triggers_suggestion(self):
        long_title = "A" * 70
        result = score_content(
            "Some words " * 100,
            title=long_title,
            meta_description="A reasonable meta description for the page content here.",
            keywords=["words"],
        )
        assert any("title" in s.lower() for s in result.suggestions)

    def test_no_headings_triggers_suggestion(self):
        text = "Just plain text with no headings at all. " * 50
        result = score_content(
            text,
            title="A Good Title That Is Thirty Plus Chars",
            meta_description="A reasonable meta description for the page content here.",
            keywords=["text"],
        )
        assert any("heading" in s.lower() for s in result.suggestions)


class TestOutlineEdgeCases:
    """Edge cases for outline generation."""

    def test_single_keyword_outline(self):
        outline = generate_outline("Testing", ["testing"])
        assert len(outline.target_keywords) == 1
        assert outline.sections[0]["heading"].startswith("What is")

    def test_outline_custom_word_count(self):
        outline = generate_outline("AI", ["ai", "ml"], target_words=3000)
        assert outline.estimated_word_count == 3000
