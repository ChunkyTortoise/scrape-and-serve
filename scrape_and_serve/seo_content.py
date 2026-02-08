"""SEO content generation: keyword analysis, outline generation, draft scoring."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class KeywordAnalysis:
    """Analysis of keyword usage in content."""

    keyword: str
    count: int
    density: float  # percentage of total words
    in_title: bool
    in_first_paragraph: bool


@dataclass
class ContentOutline:
    """Structured outline for an article."""

    title: str
    meta_description: str
    sections: list[dict[str, str]]  # {"heading": ..., "notes": ...}
    target_keywords: list[str]
    estimated_word_count: int


@dataclass
class SEOScore:
    """SEO score breakdown for content."""

    total_score: int  # 0-100
    word_count: int
    keyword_scores: list[KeywordAnalysis]
    has_meta_description: bool
    heading_count: int
    readability_grade: float
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


def count_keyword(text: str, keyword: str) -> int:
    """Count occurrences of a keyword (case-insensitive)."""
    return len(re.findall(re.escape(keyword), text, re.IGNORECASE))


def keyword_density(text: str, keyword: str) -> float:
    """Calculate keyword density as percentage of total words."""
    words = text.split()
    if not words:
        return 0.0
    kw_count = count_keyword(text, keyword)
    kw_words = len(keyword.split())
    return round((kw_count * kw_words / len(words)) * 100, 2)


def analyze_keyword(text: str, keyword: str, title: str = "") -> KeywordAnalysis:
    """Analyze keyword usage in content."""
    paragraphs = text.split("\n\n")
    first_para = paragraphs[0] if paragraphs else ""

    return KeywordAnalysis(
        keyword=keyword,
        count=count_keyword(text, keyword),
        density=keyword_density(text, keyword),
        in_title=keyword.lower() in title.lower() if title else False,
        in_first_paragraph=keyword.lower() in first_para.lower(),
    )


def generate_outline(
    topic: str,
    keywords: list[str],
    num_sections: int = 5,
    target_words: int = 1500,
) -> ContentOutline:
    """Generate a content outline from a topic and keywords."""
    sections = [
        {"heading": f"What is {topic}?", "notes": f"Define {topic} and why it matters."},
        {"heading": f"Key Benefits of {topic}", "notes": "List 3-5 benefits with examples."},
    ]

    if len(keywords) > 1:
        for kw in keywords[1 : num_sections - 2]:
            sections.append(
                {
                    "heading": f"How {kw} Relates to {topic}",
                    "notes": f"Explore the connection between {kw} and {topic}.",
                }
            )

    sections.append({"heading": "Getting Started", "notes": "Actionable steps for the reader."})
    sections.append({"heading": "Conclusion", "notes": f"Summarize key points about {topic}."})

    return ContentOutline(
        title=f"The Complete Guide to {topic}",
        meta_description=f"Learn everything about {topic}. Covers {', '.join(keywords[:3])}.",
        sections=sections[:num_sections],
        target_keywords=keywords,
        estimated_word_count=target_words,
    )


def _average_sentence_length(text: str) -> float:
    """Calculate average sentence length."""
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return 0.0
    total_words = sum(len(s.split()) for s in sentences)
    return total_words / len(sentences)


def _average_word_length(text: str) -> float:
    """Calculate average word length (syllable proxy)."""
    words = re.findall(r"\b\w+\b", text)
    if not words:
        return 0.0
    return sum(len(w) for w in words) / len(words)


def readability_score(text: str) -> float:
    """Simple readability grade (approximate Flesch-Kincaid grade level)."""
    avg_sentence = _average_sentence_length(text)
    avg_word = _average_word_length(text)
    # Simplified Flesch-Kincaid approximation
    grade = 0.39 * avg_sentence + 11.8 * (avg_word / 3.0) - 15.59
    return round(max(0, grade), 1)


def score_content(
    text: str,
    title: str,
    meta_description: str,
    keywords: list[str],
) -> SEOScore:
    """Score content for SEO quality (0-100)."""
    word_count = len(text.split())
    headings = re.findall(r"^#{1,6}\s", text, re.MULTILINE)
    heading_count = len(headings)

    keyword_scores = [analyze_keyword(text, kw, title) for kw in keywords]
    readability = readability_score(text)

    score = 0
    issues: list[str] = []
    suggestions: list[str] = []

    # Word count (0-20)
    if word_count >= 1500:
        score += 20
    elif word_count >= 800:
        score += 15
    elif word_count >= 300:
        score += 10
    else:
        score += 5
        issues.append(f"Content too short ({word_count} words). Aim for 1500+.")

    # Meta description (0-10)
    has_meta = bool(meta_description and 50 <= len(meta_description) <= 160)
    if has_meta:
        score += 10
    else:
        issues.append("Meta description should be 50-160 characters.")

    # Title (0-10)
    if title and 30 <= len(title) <= 65:
        score += 10
    else:
        suggestions.append("Title should be 30-65 characters.")

    # Keywords (0-30)
    for ka in keyword_scores:
        if 0.5 <= ka.density <= 3.0:
            score += 8
        elif ka.count > 0:
            score += 4
        else:
            issues.append(f'Keyword "{ka.keyword}" not found in content.')

        if ka.in_title:
            score += 4
        if ka.in_first_paragraph:
            score += 3

    score = min(score, 60)  # cap keyword portion

    # Headings (0-15)
    if heading_count >= 3:
        score += 15
    elif heading_count >= 1:
        score += 8
    else:
        suggestions.append("Add headings (H2, H3) to structure content.")

    # Readability (0-15)
    if 6 <= readability <= 12:
        score += 15
    elif readability < 6:
        score += 10
        suggestions.append("Content may be too simple for the audience.")
    else:
        score += 5
        suggestions.append("Content readability is high. Simplify sentences.")

    return SEOScore(
        total_score=min(score, 100),
        word_count=word_count,
        keyword_scores=keyword_scores,
        has_meta_description=has_meta,
        heading_count=heading_count,
        readability_grade=readability,
        issues=issues,
        suggestions=suggestions,
    )
