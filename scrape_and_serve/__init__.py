"""Scrape-and-Serve: Web scraping framework + Excel-to-web converter."""

__version__ = "0.1.0"

from scrape_and_serve.diff_visualizer import DiffResult, DiffVisualizer, PageSnapshot
from scrape_and_serve.scheduler import JobStatus, ScheduleConfig, SchedulerStatus, ScrapeScheduler
from scrape_and_serve.seo_analyzer import (
    ContentComparison,
    KeywordSuggestion,
    SEOAnalysis,
    SEOAnalyzer,
    TechnicalIssue,
)
from scrape_and_serve.validator import DataValidator, ValidationError, ValidationResult, ValidationRule

__all__ = [
    "ContentComparison",
    "DataValidator",
    "DiffResult",
    "DiffVisualizer",
    "JobStatus",
    "KeywordSuggestion",
    "PageSnapshot",
    "SEOAnalysis",
    "SEOAnalyzer",
    "ScheduleConfig",
    "SchedulerStatus",
    "ScrapeScheduler",
    "TechnicalIssue",
    "ValidationError",
    "ValidationResult",
    "ValidationRule",
]
