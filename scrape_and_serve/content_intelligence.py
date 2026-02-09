"""Content intelligence for text analysis, sentiment, and entity detection."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

_POSITIVE_WORDS: set[str] = {
    "good",
    "great",
    "excellent",
    "amazing",
    "wonderful",
    "fantastic",
    "best",
    "love",
    "happy",
    "positive",
    "beautiful",
    "perfect",
    "brilliant",
    "superb",
    "outstanding",
    "remarkable",
    "impressive",
    "delightful",
    "enjoy",
    "glad",
    "pleased",
    "satisfied",
    "helpful",
    "friendly",
    "awesome",
    "nice",
    "fine",
    "success",
    "win",
    "advantage",
    "benefit",
    "improve",
    "growth",
    "gain",
    "profit",
    "progress",
    "innovation",
    "creative",
    "efficient",
    "effective",
    "reliable",
    "strong",
    "exciting",
    "promising",
    "optimistic",
    "thriving",
    "exceptional",
    "superior",
    "magnificent",
    "joyful",
    "grateful",
}

_NEGATIVE_WORDS: set[str] = {
    "bad",
    "terrible",
    "awful",
    "horrible",
    "worst",
    "hate",
    "ugly",
    "poor",
    "negative",
    "sad",
    "angry",
    "disappointing",
    "failure",
    "problem",
    "issue",
    "broken",
    "useless",
    "waste",
    "difficult",
    "painful",
    "annoying",
    "boring",
    "confused",
    "frustrated",
    "worried",
    "afraid",
    "weak",
    "slow",
    "expensive",
    "loss",
    "decline",
    "risk",
    "danger",
    "threat",
    "crisis",
    "damage",
    "harm",
    "error",
    "mistake",
    "fault",
    "flaw",
    "bug",
    "crash",
    "fail",
    "reject",
    "complaint",
    "concern",
    "lacking",
    "inferior",
    "mediocre",
    "dreadful",
}

_DEFAULT_CATEGORIES: list[str] = [
    "technology",
    "business",
    "science",
    "health",
    "sports",
    "entertainment",
    "politics",
    "education",
    "finance",
    "general",
]

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "technology": ["software", "app", "code", "data", "ai", "computer", "digital", "tech", "algorithm", "api"],
    "business": ["company", "market", "revenue", "startup", "enterprise", "strategy", "management", "profit"],
    "science": ["research", "study", "experiment", "hypothesis", "theory", "lab", "discovery", "biology"],
    "health": ["medical", "health", "doctor", "patient", "treatment", "disease", "wellness", "fitness"],
    "sports": ["game", "team", "player", "score", "match", "championship", "athlete", "tournament"],
    "entertainment": ["movie", "music", "show", "film", "artist", "concert", "performance", "media"],
    "politics": ["government", "policy", "election", "vote", "law", "political", "congress", "senate"],
    "education": ["school", "student", "learn", "teach", "university", "course", "training", "academic"],
    "finance": ["investment", "stock", "bank", "trading", "fund", "portfolio", "financial", "currency"],
}


@dataclass
class ContentAnalysis:
    """Result of content analysis."""

    topics: list[str] = field(default_factory=list)
    sentiment_score: float = 0.0
    word_count: int = 0
    reading_time_minutes: float = 0.0
    language_complexity: float = 0.0
    entities: list[str] = field(default_factory=list)
    category: str = "general"


class ContentAnalyzer:
    """Analyzes text content for topics, sentiment, entities, and categories."""

    def __init__(self) -> None:
        pass

    def analyze(self, text: str) -> ContentAnalysis:
        """Run full content analysis on text."""
        if not text.strip():
            return ContentAnalysis()

        words = text.split()
        word_count = len(words)
        reading_time = word_count / 200.0  # ~200 wpm average

        return ContentAnalysis(
            topics=self.extract_topics(text),
            sentiment_score=self.score_sentiment(text),
            word_count=word_count,
            reading_time_minutes=round(reading_time, 2),
            language_complexity=self._compute_complexity(text),
            entities=self.detect_entities(text),
            category=self.categorize(text),
        )

    def extract_topics(self, text: str, top_k: int = 5) -> list[str]:
        """Extract top topics using word frequency (stop words excluded)."""
        if not text.strip():
            return []

        stop_words = {
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
            "and",
            "but",
            "or",
            "not",
            "no",
            "nor",
            "so",
            "yet",
            "both",
            "either",
            "neither",
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
            "she",
            "they",
            "them",
            "their",
            "what",
            "which",
            "who",
            "whom",
            "how",
            "when",
            "where",
            "why",
            "all",
            "each",
            "every",
            "if",
            "then",
            "than",
            "very",
            "just",
            "about",
            "up",
            "out",
            "also",
        }

        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        filtered = [w for w in words if w not in stop_words]
        if not filtered:
            return []

        counts = Counter(filtered)
        return [word for word, _ in counts.most_common(top_k)]

    def score_sentiment(self, text: str) -> float:
        """Score sentiment using keyword matching. Returns -1 to 1."""
        if not text.strip():
            return 0.0

        words = set(re.findall(r"\b[a-zA-Z]+\b", text.lower()))
        pos_count = len(words & _POSITIVE_WORDS)
        neg_count = len(words & _NEGATIVE_WORDS)
        total = pos_count + neg_count

        if total == 0:
            return 0.0

        score = (pos_count - neg_count) / total
        return round(max(-1.0, min(1.0, score)), 4)

    def detect_entities(self, text: str) -> list[str]:
        """Detect proper nouns / entities (capitalized multi-word sequences)."""
        if not text.strip():
            return []

        # Find capitalized words not at sentence start
        entities: list[str] = []
        # Multi-word capitalized sequences
        pattern = r"(?<!\. )(?<!\.\s)(?<!^)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)"
        for match in re.finditer(pattern, text):
            entity = match.group(1)
            if entity not in entities:
                entities.append(entity)

        # Single capitalized words not at sentence starts (heuristic)
        sentences = re.split(r"[.!?]\s+", text)
        for sentence in sentences:
            words = sentence.split()
            for word in words[1:]:  # skip first word of sentence
                clean = re.sub(r"[^a-zA-Z]", "", word)
                if clean and clean[0].isupper() and len(clean) > 1 and clean not in entities:
                    entities.append(clean)

        return entities

    def categorize(self, text: str, categories: list[str] | None = None) -> str:
        """Categorize text based on keyword matching."""
        if not text.strip():
            return "general"

        cats = categories or _DEFAULT_CATEGORIES
        lower = text.lower()
        scores: dict[str, int] = {}

        for cat in cats:
            keywords = _CATEGORY_KEYWORDS.get(cat, [])
            scores[cat] = sum(1 for kw in keywords if kw in lower)

        best = max(scores, key=lambda c: scores[c]) if scores else "general"
        return best if scores.get(best, 0) > 0 else "general"

    def analyze_batch(self, texts: list[str]) -> list[ContentAnalysis]:
        """Analyze multiple texts."""
        return [self.analyze(text) for text in texts]

    def _compute_complexity(self, text: str) -> float:
        """Compute language complexity score (0-1) based on avg word length and sentence length."""
        words = text.split()
        if not words:
            return 0.0

        avg_word_len = sum(len(w) for w in words) / len(words)
        sentences = re.split(r"[.!?]+", text)
        sentences = [s for s in sentences if s.strip()]
        avg_sent_len = len(words) / max(len(sentences), 1)

        # Normalize: avg word length ~4-10 maps to 0-1, avg sent length ~5-30 maps to 0-1
        word_score = min(max((avg_word_len - 4) / 6, 0), 1)
        sent_score = min(max((avg_sent_len - 5) / 25, 0), 1)

        return round((word_score + sent_score) / 2, 4)
