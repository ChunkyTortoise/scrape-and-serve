"""Tests for the SEO analyzer module."""

from scrape_and_serve.seo_analyzer import (
    BacklinkEstimator,
    CompetitorAnalysis,
    KeywordGapAnalysis,
    SEOAnalyzer,
    TrendTracker,
)


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


class TestCompetitorAnalysis:
    def test_empty_pages(self):
        analyzer = CompetitorAnalysis()
        result = analyzer.analyze([])
        assert result.rankings == []
        assert result.avg_score == 0.0
        assert result.top_performer == ""
        assert result.bottom_performer == ""

    def test_single_page(self):
        analyzer = CompetitorAnalysis()
        pages = [{"url": "https://example.com", "score": 75.5}]
        result = analyzer.analyze(pages)
        assert len(result.rankings) == 1
        assert result.rankings[0] == ("https://example.com", 75.5)
        assert result.avg_score == 75.5
        assert result.top_performer == "https://example.com"
        assert result.bottom_performer == "https://example.com"

    def test_multiple_pages_ranked(self):
        analyzer = CompetitorAnalysis()
        pages = [
            {"url": "https://a.com", "score": 60},
            {"url": "https://b.com", "score": 85},
            {"url": "https://c.com", "score": 70},
        ]
        result = analyzer.analyze(pages)
        assert len(result.rankings) == 3
        assert result.rankings[0] == ("https://b.com", 85)
        assert result.rankings[2] == ("https://a.com", 60)
        assert result.top_performer == "https://b.com"
        assert result.bottom_performer == "https://a.com"
        assert result.avg_score == 71.67


class TestKeywordGapAnalysis:
    def test_no_overlap(self):
        analyzer = KeywordGapAnalysis()
        yours = {"python", "django"}
        theirs = {"javascript", "react"}
        result = analyzer.find_gaps(yours, theirs)
        assert set(result.missing_keywords) == {"javascript", "react"}
        assert result.shared_keywords == []
        assert set(result.unique_keywords) == {"python", "django"}
        assert result.gap_count == 2

    def test_complete_overlap(self):
        analyzer = KeywordGapAnalysis()
        yours = {"python", "web", "scraping"}
        theirs = {"python", "web", "scraping"}
        result = analyzer.find_gaps(yours, theirs)
        assert result.missing_keywords == []
        assert set(result.shared_keywords) == {"python", "web", "scraping"}
        assert result.unique_keywords == []
        assert result.gap_count == 0

    def test_partial_overlap(self):
        analyzer = KeywordGapAnalysis()
        yours = {"python", "web", "scraping", "beautiful"}
        theirs = {"python", "web", "automation", "selenium"}
        result = analyzer.find_gaps(yours, theirs)
        assert set(result.missing_keywords) == {"automation", "selenium"}
        assert set(result.shared_keywords) == {"python", "web"}
        assert set(result.unique_keywords) == {"scraping", "beautiful"}
        assert result.gap_count == 2


class TestBacklinkEstimator:
    def test_no_links(self):
        estimator = BacklinkEstimator()
        html = "<html><body><p>No links here</p></body></html>"
        result = estimator.estimate(html)
        assert result.internal_count == 0
        assert result.external_count == 0
        assert result.quality_score == 0.0
        assert result.domains == []

    def test_internal_links_only(self):
        estimator = BacklinkEstimator()
        html = '<html><body><a href="/page1">P1</a><a href="/page2">P2</a></body></html>'
        result = estimator.estimate(html)
        assert result.internal_count == 2
        assert result.external_count == 0
        assert result.quality_score == 10.0

    def test_external_links_only(self):
        estimator = BacklinkEstimator()
        html = '<html><body><a href="https://example.com">Ex</a></body></html>'
        result = estimator.estimate(html)
        assert result.internal_count == 0
        assert result.external_count == 1
        assert result.quality_score == 20.0

    def test_mixed_links_good_quality(self):
        estimator = BacklinkEstimator()
        html = """
        <html><body>
            <a href="/page1">P1</a>
            <a href="/page2">P2</a>
            <a href="/page3">P3</a>
            <a href="https://domain1.com">D1</a>
            <a href="https://domain2.com">D2</a>
            <a href="https://domain3.com">D3</a>
        </body></html>
        """
        result = estimator.estimate(html)
        assert result.internal_count == 3
        assert result.external_count == 3
        assert result.quality_score > 50
        assert len(result.domains) == 3


class TestTrendTracker:
    def test_empty_history(self):
        tracker = TrendTracker()
        result = tracker.track([])
        assert result.trend_direction == "stable"
        assert result.avg_change == 0.0
        assert result.forecast == 0.0
        assert result.data_points == 0

    def test_single_data_point(self):
        tracker = TrendTracker()
        history = [{"timestamp": 1, "score": 75.0}]
        result = tracker.track(history)
        assert result.trend_direction == "stable"
        assert result.avg_change == 0.0
        assert result.forecast == 75.0
        assert result.data_points == 1

    def test_improving_trend(self):
        tracker = TrendTracker()
        history = [
            {"timestamp": 1, "score": 50.0},
            {"timestamp": 2, "score": 55.0},
            {"timestamp": 3, "score": 60.0},
        ]
        result = tracker.track(history)
        assert result.trend_direction == "improving"
        assert result.avg_change == 5.0
        assert result.forecast == 65.0
        assert result.data_points == 3

    def test_declining_trend(self):
        tracker = TrendTracker()
        history = [
            {"timestamp": 1, "score": 80.0},
            {"timestamp": 2, "score": 75.0},
            {"timestamp": 3, "score": 70.0},
        ]
        result = tracker.track(history)
        assert result.trend_direction == "declining"
        assert result.avg_change == -5.0
        assert result.forecast == 65.0

    def test_stable_trend(self):
        tracker = TrendTracker()
        history = [
            {"timestamp": 1, "score": 70.0},
            {"timestamp": 2, "score": 71.0},
            {"timestamp": 3, "score": 70.5},
        ]
        result = tracker.track(history)
        assert result.trend_direction == "stable"
        assert abs(result.avg_change) < 2.0
