"""Tests for content intelligence analyzer."""

from __future__ import annotations

from scrape_and_serve.content_intelligence import ContentAnalysis, ContentAnalyzer


class TestContentAnalyzer:
    def test_positive_sentiment(self) -> None:
        analyzer = ContentAnalyzer()
        score = analyzer.score_sentiment("This is great and amazing and wonderful")
        assert score > 0

    def test_negative_sentiment(self) -> None:
        analyzer = ContentAnalyzer()
        score = analyzer.score_sentiment("This is terrible and awful and horrible")
        assert score < 0

    def test_neutral_sentiment(self) -> None:
        analyzer = ContentAnalyzer()
        score = analyzer.score_sentiment("The table has four legs")
        assert score == 0.0

    def test_sentiment_range(self) -> None:
        analyzer = ContentAnalyzer()
        score = analyzer.score_sentiment("great amazing excellent wonderful fantastic")
        assert -1.0 <= score <= 1.0

    def test_topic_extraction(self) -> None:
        analyzer = ContentAnalyzer()
        text = "Python programming language is used for software development and data science applications"
        topics = analyzer.extract_topics(text, top_k=3)
        assert len(topics) <= 3
        assert len(topics) > 0

    def test_topic_extraction_empty(self) -> None:
        analyzer = ContentAnalyzer()
        assert analyzer.extract_topics("") == []

    def test_entity_detection(self) -> None:
        analyzer = ContentAnalyzer()
        text = "The meeting with John Smith was about Google and Microsoft products."
        entities = analyzer.detect_entities(text)
        assert len(entities) > 0
        # Should find at least one capitalized entity
        assert any("John" in e or "Smith" in e or "Google" in e or "Microsoft" in e for e in entities)

    def test_entity_detection_empty(self) -> None:
        analyzer = ContentAnalyzer()
        assert analyzer.detect_entities("") == []

    def test_categorize_technology(self) -> None:
        analyzer = ContentAnalyzer()
        text = "The new software application uses advanced AI algorithms and computer code"
        cat = analyzer.categorize(text)
        assert cat == "technology"

    def test_categorize_business(self) -> None:
        analyzer = ContentAnalyzer()
        text = "The company reported strong revenue growth and market strategy"
        cat = analyzer.categorize(text)
        assert cat == "business"

    def test_categorize_default(self) -> None:
        analyzer = ContentAnalyzer()
        text = "some random words here with nothing specific"
        cat = analyzer.categorize(text)
        assert cat == "general"

    def test_categorize_custom_categories(self) -> None:
        analyzer = ContentAnalyzer()
        text = "The football team scored a goal"
        cat = analyzer.categorize(text, categories=["sports", "general"])
        assert cat in ["sports", "general"]

    def test_analyze_full(self) -> None:
        analyzer = ContentAnalyzer()
        text = "The AI software company Google announced great progress in technology research."
        result = analyzer.analyze(text)
        assert isinstance(result, ContentAnalysis)
        assert result.word_count > 0
        assert result.reading_time_minutes > 0
        assert isinstance(result.topics, list)
        assert isinstance(result.entities, list)
        assert result.category in ["technology", "business", "science", "general"]

    def test_analyze_empty(self) -> None:
        analyzer = ContentAnalyzer()
        result = analyzer.analyze("")
        assert result.word_count == 0
        assert result.sentiment_score == 0.0
        assert result.topics == []

    def test_analyze_short_text(self) -> None:
        analyzer = ContentAnalyzer()
        result = analyzer.analyze("Hello world")
        assert result.word_count == 2

    def test_reading_time(self) -> None:
        analyzer = ContentAnalyzer()
        text = " ".join(["word"] * 200)  # 200 words = ~1 minute
        result = analyzer.analyze(text)
        assert 0.9 <= result.reading_time_minutes <= 1.1

    def test_batch_analysis(self) -> None:
        analyzer = ContentAnalyzer()
        texts = ["Great software", "Terrible mistake", "Normal text"]
        results = analyzer.analyze_batch(texts)
        assert len(results) == 3
        assert results[0].sentiment_score > results[1].sentiment_score

    def test_batch_empty_list(self) -> None:
        analyzer = ContentAnalyzer()
        assert analyzer.analyze_batch([]) == []

    def test_language_complexity(self) -> None:
        analyzer = ContentAnalyzer()
        simple = "I am a cat."
        complex_text = (
            "The unprecedented conflagration necessitated an extraordinarily "
            "comprehensive investigation into the multifaceted circumstances "
            "surrounding the catastrophically devastating infrastructure deterioration."
        )
        r1 = analyzer.analyze(simple)
        r2 = analyzer.analyze(complex_text)
        assert r2.language_complexity > r1.language_complexity

    def test_sentiment_empty(self) -> None:
        analyzer = ContentAnalyzer()
        assert analyzer.score_sentiment("") == 0.0

    def test_entities_no_proper_nouns(self) -> None:
        analyzer = ContentAnalyzer()
        entities = analyzer.detect_entities("the quick brown fox jumps over the lazy dog")
        assert entities == []
