"""Advanced SEO analysis: keyword suggestions, content comparison, technical issues."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass


@dataclass
class KeywordSuggestion:
    """A suggested keyword with relevance score."""

    keyword: str
    frequency: int
    tfidf_score: float
    is_ngram: bool  # True if multi-word


@dataclass
class ContentComparison:
    """Comparison of two pages for SEO."""

    page_a_url: str
    page_b_url: str
    shared_keywords: list[str]
    unique_to_a: list[str]
    unique_to_b: list[str]
    similarity_score: float  # 0-1


@dataclass
class TechnicalIssue:
    """A detected technical SEO issue."""

    issue_type: str  # e.g., "missing_title", "slow_loading", "no_meta"
    severity: str  # "high", "medium", "low"
    description: str
    suggestion: str


@dataclass
class SEOAnalysis:
    """Complete SEO analysis result."""

    url: str
    keyword_suggestions: list[KeywordSuggestion]
    technical_issues: list[TechnicalIssue]
    content_score: float  # 0-100
    word_count: int
    heading_count: int
    link_count: int
    image_count: int


class SEOAnalyzer:
    """Advanced SEO analysis beyond basic scoring.

    Provides keyword suggestions via TF-IDF n-gram extraction,
    content comparison between pages, and technical issue detection.
    """

    # Common stop words to filter
    STOP_WORDS = frozenset(
        [
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "shall",
            "can",
            "need",
            "dare",
            "ought",
            "used",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "out",
            "off",
            "over",
            "under",
            "again",
            "further",
            "then",
            "once",
            "and",
            "but",
            "or",
            "nor",
            "not",
            "so",
            "yet",
            "both",
            "each",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "only",
            "own",
            "same",
            "than",
            "too",
            "very",
            "just",
            "because",
            "this",
            "that",
            "these",
            "those",
            "it",
            "its",
            "i",
            "me",
            "my",
            "we",
            "our",
            "you",
            "your",
            "he",
            "him",
            "his",
            "she",
            "her",
            "they",
            "them",
            "their",
            "what",
            "which",
            "who",
            "whom",
        ]
    )

    def _tokenize(self, text: str) -> list[str]:
        """Lowercase and extract word tokens from text."""
        return re.findall(r"[a-z0-9]+", text.lower())

    def _strip_html(self, html: str) -> str:
        """Remove HTML tags and return plain text."""
        return re.sub(r"<[^>]+>", " ", html)

    def extract_keywords(self, text: str, top_n: int = 20) -> list[KeywordSuggestion]:
        """Extract keyword suggestions using TF-IDF-like scoring.

        Extracts both unigrams and bigrams, filters stop words,
        scores by frequency * inverse document position.
        """
        tokens = self._tokenize(text)
        if not tokens:
            return []

        total_tokens = len(tokens)

        # Unigrams (filter stop words and short tokens)
        unigrams = [t for t in tokens if t not in self.STOP_WORDS and len(t) > 2]
        uni_counts = Counter(unigrams)

        # Bigrams
        bigrams: list[str] = []
        for i in range(len(tokens) - 1):
            a, b = tokens[i], tokens[i + 1]
            if a not in self.STOP_WORDS and b not in self.STOP_WORDS and len(a) > 2 and len(b) > 2:
                bigrams.append(f"{a} {b}")
        bi_counts = Counter(bigrams)

        suggestions: list[KeywordSuggestion] = []

        # Score unigrams: frequency * log(total / frequency) for IDF-like weighting
        for word, count in uni_counts.most_common(top_n * 2):
            idf = math.log(total_tokens / count) if count < total_tokens else 0.1
            score = round(count * idf, 3)
            suggestions.append(KeywordSuggestion(keyword=word, frequency=count, tfidf_score=score, is_ngram=False))

        # Score bigrams
        for bigram, count in bi_counts.most_common(top_n):
            idf = math.log(total_tokens / count) if count < total_tokens else 0.1
            score = round(count * idf * 1.5, 3)  # boost bigrams
            suggestions.append(KeywordSuggestion(keyword=bigram, frequency=count, tfidf_score=score, is_ngram=True))

        # Sort by score descending, return top_n
        suggestions.sort(key=lambda s: s.tfidf_score, reverse=True)
        return suggestions[:top_n]

    def compare_content(
        self, text_a: str, text_b: str, url_a: str = "page_a", url_b: str = "page_b"
    ) -> ContentComparison:
        """Compare two pages for keyword overlap and similarity."""
        tokens_a = set(t for t in self._tokenize(text_a) if t not in self.STOP_WORDS and len(t) > 2)
        tokens_b = set(t for t in self._tokenize(text_b) if t not in self.STOP_WORDS and len(t) > 2)

        shared = sorted(tokens_a & tokens_b)
        unique_a = sorted(tokens_a - tokens_b)
        unique_b = sorted(tokens_b - tokens_a)

        # Jaccard similarity
        union = tokens_a | tokens_b
        similarity = len(tokens_a & tokens_b) / len(union) if union else 0.0

        return ContentComparison(
            page_a_url=url_a,
            page_b_url=url_b,
            shared_keywords=shared,
            unique_to_a=unique_a,
            unique_to_b=unique_b,
            similarity_score=round(similarity, 4),
        )

    def detect_issues(self, html: str, url: str = "") -> list[TechnicalIssue]:
        """Detect technical SEO issues from HTML content.

        Checks: missing title, missing meta description, missing h1,
        too many h1s, no alt text on images, too few internal links.
        """
        issues: list[TechnicalIssue] = []

        # Missing <title>
        if not re.search(r"<title\b[^>]*>.+?</title>", html, re.IGNORECASE | re.DOTALL):
            issues.append(
                TechnicalIssue(
                    issue_type="missing_title",
                    severity="high",
                    description="Page is missing a <title> tag.",
                    suggestion="Add a unique, descriptive <title> tag (50-60 characters).",
                )
            )

        # Missing meta description
        if not re.search(r'<meta\s+[^>]*name=["\']description["\'][^>]*>', html, re.IGNORECASE):
            issues.append(
                TechnicalIssue(
                    issue_type="missing_meta_description",
                    severity="high",
                    description="Page is missing a meta description.",
                    suggestion="Add a <meta name='description'> tag (120-160 characters).",
                )
            )

        # Missing h1
        h1_matches = re.findall(r"<h1\b[^>]*>", html, re.IGNORECASE)
        if not h1_matches:
            issues.append(
                TechnicalIssue(
                    issue_type="missing_h1",
                    severity="high",
                    description="Page has no <h1> heading.",
                    suggestion="Add exactly one <h1> tag with the primary keyword.",
                )
            )
        elif len(h1_matches) > 1:
            issues.append(
                TechnicalIssue(
                    issue_type="multiple_h1",
                    severity="medium",
                    description=f"Page has {len(h1_matches)} <h1> tags (should be 1).",
                    suggestion="Use only one <h1> tag per page; use <h2>-<h6> for sub-headings.",
                )
            )

        # Images without alt text
        img_tags = re.findall(r"<img\b[^>]*>", html, re.IGNORECASE)
        imgs_no_alt = [tag for tag in img_tags if not re.search(r'alt=["\'][^"\']+["\']', tag, re.IGNORECASE)]
        if imgs_no_alt:
            issues.append(
                TechnicalIssue(
                    issue_type="images_missing_alt",
                    severity="medium",
                    description=f"{len(imgs_no_alt)} image(s) missing alt text.",
                    suggestion="Add descriptive alt attributes to all <img> tags.",
                )
            )

        # Too few links
        link_count = len(re.findall(r"<a\b[^>]*href=", html, re.IGNORECASE))
        if link_count < 2:
            issues.append(
                TechnicalIssue(
                    issue_type="too_few_links",
                    severity="low",
                    description=f"Page has only {link_count} link(s).",
                    suggestion="Add internal and external links to improve SEO.",
                )
            )

        return issues

    def analyze(self, html: str, url: str = "") -> SEOAnalysis:
        """Full SEO analysis of an HTML page."""
        plain_text = self._strip_html(html)
        keywords = self.extract_keywords(plain_text)
        issues = self.detect_issues(html, url)

        word_count = len(plain_text.split())
        heading_count = len(re.findall(r"<h[1-6]\b", html, re.IGNORECASE))
        link_count = len(re.findall(r"<a\b[^>]*href=", html, re.IGNORECASE))
        image_count = len(re.findall(r"<img\b", html, re.IGNORECASE))

        # Content score: based on word count, headings, issues
        score = 50.0
        if word_count >= 1000:
            score += 20
        elif word_count >= 300:
            score += 10
        else:
            score -= 10

        if heading_count >= 3:
            score += 15
        elif heading_count >= 1:
            score += 5

        # Penalize for issues
        for issue in issues:
            if issue.severity == "high":
                score -= 10
            elif issue.severity == "medium":
                score -= 5
            elif issue.severity == "low":
                score -= 2

        score = max(0.0, min(100.0, score))

        return SEOAnalysis(
            url=url,
            keyword_suggestions=keywords,
            technical_issues=issues,
            content_score=round(score, 1),
            word_count=word_count,
            heading_count=heading_count,
            link_count=link_count,
            image_count=image_count,
        )
