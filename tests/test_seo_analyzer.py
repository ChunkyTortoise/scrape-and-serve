"""Tests for the SEO analyzer module."""

from scrape_and_serve.seo_analyzer import SEOAnalyzer


class TestKeywordExtraction:
    def test_extracts_keywords(self):
        analyzer = SEOAnalyzer()
        text = (
            "Python web scraping is powerful. Python makes data extraction easy. Web scraping with Python is popular."
        )
        keywords = analyzer.extract_keywords(text, top_n=10)
        assert len(keywords) > 0
        keyword_words = [k.keyword for k in keywords]
        assert "python" in keyword_words

    def test_filters_stopwords(self):
        analyzer = SEOAnalyzer()
        text = "the quick brown fox jumps over the lazy dog and the cat is on the mat"
        keywords = analyzer.extract_keywords(text, top_n=10)
        keyword_words = [k.keyword for k in keywords]
        # "the", "and", "is", "on" should not appear
        for stop in ["the", "and", "is", "on"]:
            assert stop not in keyword_words

    def test_includes_bigrams(self):
        analyzer = SEOAnalyzer()
        text = (
            "machine learning is transforming industries. "
            "machine learning applications are growing. "
            "deep learning and machine learning are related."
        )
        keywords = analyzer.extract_keywords(text, top_n=20)
        bigrams = [k for k in keywords if k.is_ngram]
        assert len(bigrams) > 0

    def test_empty_text(self):
        analyzer = SEOAnalyzer()
        keywords = analyzer.extract_keywords("", top_n=10)
        assert keywords == []


class TestContentComparison:
    def test_similar_content(self):
        analyzer = SEOAnalyzer()
        text_a = "Python web scraping tutorial with BeautifulSoup and requests library"
        text_b = "Python web scraping guide using BeautifulSoup and httpx library"
        result = analyzer.compare_content(text_a, text_b)
        assert result.similarity_score > 0.3
        assert len(result.shared_keywords) > 0

    def test_different_content(self):
        analyzer = SEOAnalyzer()
        text_a = "Python programming language tutorial for beginners"
        text_b = "Cooking Italian pasta recipes with fresh ingredients"
        result = analyzer.compare_content(text_a, text_b)
        assert result.similarity_score < 0.3

    def test_shared_keywords(self):
        analyzer = SEOAnalyzer()
        text_a = "data science python analytics"
        text_b = "data engineering python pipelines"
        result = analyzer.compare_content(text_a, text_b, url_a="page1", url_b="page2")
        assert "python" in result.shared_keywords
        assert "data" in result.shared_keywords
        assert result.page_a_url == "page1"
        assert result.page_b_url == "page2"


class TestTechnicalIssues:
    def test_missing_title(self):
        analyzer = SEOAnalyzer()
        html = "<html><head></head><body><p>Hello</p></body></html>"
        issues = analyzer.detect_issues(html)
        issue_types = [i.issue_type for i in issues]
        assert "missing_title" in issue_types

    def test_missing_meta(self):
        analyzer = SEOAnalyzer()
        html = "<html><head><title>Test</title></head><body><h1>Hello</h1></body></html>"
        issues = analyzer.detect_issues(html)
        issue_types = [i.issue_type for i in issues]
        assert "missing_meta_description" in issue_types

    def test_multiple_h1(self):
        analyzer = SEOAnalyzer()
        html = (
            "<html><head><title>Test</title>"
            '<meta name="description" content="A test page">'
            "</head><body>"
            "<h1>First</h1><h1>Second</h1>"
            '<a href="/link1">Link 1</a><a href="/link2">Link 2</a>'
            "</body></html>"
        )
        issues = analyzer.detect_issues(html)
        issue_types = [i.issue_type for i in issues]
        assert "multiple_h1" in issue_types

    def test_clean_html(self):
        analyzer = SEOAnalyzer()
        html = (
            "<html><head>"
            "<title>Well Formed Page Title</title>"
            '<meta name="description" content="A properly described page with all SEO elements.">'
            "</head><body>"
            "<h1>Main Heading</h1>"
            "<p>Content here.</p>"
            '<a href="/about">About</a>'
            '<a href="/contact">Contact</a>'
            '<img src="photo.jpg" alt="A descriptive alt text">'
            "</body></html>"
        )
        issues = analyzer.detect_issues(html)
        assert len(issues) == 0


class TestAnalyze:
    def test_full_analysis(self):
        analyzer = SEOAnalyzer()
        html = (
            "<html><head>"
            "<title>Python Web Scraping Guide</title>"
            '<meta name="description" content="Learn Python web scraping with this comprehensive guide.">'
            "</head><body>"
            "<h1>Python Web Scraping</h1>"
            "<h2>Getting Started</h2>"
            "<p>" + "Python web scraping tutorial content. " * 80 + "</p>"
            "<h2>Advanced Techniques</h2>"
            "<p>" + "Advanced scraping methods and tools. " * 40 + "</p>"
            '<a href="/next">Next article</a>'
            '<a href="/prev">Previous article</a>'
            '<img src="diagram.png" alt="Scraping diagram">'
            "</body></html>"
        )
        result = analyzer.analyze(html, url="https://example.com/guide")
        assert result.url == "https://example.com/guide"
        assert result.word_count > 100
        assert result.heading_count >= 3
        assert result.link_count >= 2
        assert result.image_count >= 1
        assert 0 <= result.content_score <= 100
        assert isinstance(result.keyword_suggestions, list)
        assert isinstance(result.technical_issues, list)
