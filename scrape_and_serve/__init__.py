"""Scrape-and-Serve: Web scraping framework + Excel-to-web converter."""

__version__ = "0.1.0"

from scrape_and_serve.diff_visualizer import DiffResult, DiffVisualizer, PageSnapshot
from scrape_and_serve.scheduler import JobHistoryEntry, JobStatus, ScheduleConfig, SchedulerStatus, ScrapeScheduler, parse_cron
from scrape_and_serve.seo_analyzer import (
    BacklinkEstimator,
    BacklinkResult,
    CompetitorAnalysis,
    CompetitorResult,
    ContentComparison,
    GapResult,
    KeywordGapAnalysis,
    KeywordSuggestion,
    SEOAnalysis,
    SEOAnalyzer,
    TechnicalIssue,
    TrendResult,
    TrendTracker,
)
from scrape_and_serve.validator import (
    ConfigValidator,
    DataValidator,
    ScrapedDataValidator,
    SelectorValidator,
    URLValidator,
    ValidationError,
    ValidationResult,
    ValidationRule,
)
from scrape_and_serve.validators import validate_config, validate_scrape_result, validate_url

__all__ = [
    "BacklinkEstimator",
    "BacklinkResult",
    "CompetitorAnalysis",
    "CompetitorResult",
    "ConfigValidator",
    "ContentComparison",
    "DataValidator",
    "DiffResult",
    "DiffVisualizer",
    "GapResult",
    "JobHistoryEntry",
    "JobStatus",
    "KeywordGapAnalysis",
    "KeywordSuggestion",
    "PageSnapshot",
    "SEOAnalysis",
    "SEOAnalyzer",
    "ScheduleConfig",
    "SchedulerStatus",
    "ScrapedDataValidator",
    "ScrapeScheduler",
    "SelectorValidator",
    "TechnicalIssue",
    "TrendResult",
    "TrendTracker",
    "URLValidator",
    "ValidationError",
    "ValidationResult",
    "ValidationRule",
    "parse_cron",
    "validate_config",
    "validate_scrape_result",
    "validate_url",
]
