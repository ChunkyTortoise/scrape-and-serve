"""Scheduled scraping: asyncio-based scheduling with status tracking and callbacks."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable

logger = logging.getLogger("scrape_and_serve.scheduler")


@dataclass
class ScheduleConfig:
    """Configuration for a scheduled scrape job."""

    url: str
    interval_seconds: int = 3600  # default: hourly
    name: str = ""
    enabled: bool = True
    cron: str = ""  # cron expression, takes precedence over interval_seconds


@dataclass
class JobHistoryEntry:
    """A single job execution history entry."""

    timestamp: float
    success: bool
    result: Any = None
    error: str | None = None


@dataclass
class JobStatus:
    """Status of a scheduled job."""

    name: str
    url: str
    last_run: float | None = None
    next_run: float | None = None
    run_count: int = 0
    error_count: int = 0
    last_error: str | None = None
    is_running: bool = False
    last_result: Any = None
    history: list[JobHistoryEntry] = field(default_factory=list)


@dataclass
class SchedulerStatus:
    """Overall scheduler status."""

    is_running: bool
    total_jobs: int
    active_jobs: int
    total_runs: int
    total_errors: int
    jobs: list[JobStatus] = field(default_factory=list)


def parse_cron(cron_expr: str) -> int | None:
    """Parse a simple cron expression to interval seconds.

    Supports basic patterns like:
    - "*/N * * * *" = every N minutes
    - "0 * * * *" = every hour
    - "0 0 * * *" = every day

    Returns interval in seconds, or None if invalid/unsupported.
    """
    if not cron_expr:
        return None

    parts = cron_expr.strip().split()
    if len(parts) != 5:
        return None

    minute, hour, day, month, weekday = parts

    # Pattern: */N * * * * (every N minutes)
    if minute.startswith("*/") and hour == "*" and day == "*":
        try:
            interval_minutes = int(minute[2:])
            return interval_minutes * 60
        except ValueError:
            return None

    # Pattern: 0 * * * * (every hour)
    if minute == "0" and hour == "*" and day == "*":
        return 3600

    # Pattern: 0 0 * * * (every day at midnight)
    if minute == "0" and hour == "0" and day == "*":
        return 86400

    return None


class ScrapeScheduler:
    """Asyncio-based scrape scheduler with status tracking.

    Manages multiple scheduled scrape jobs with error tracking,
    change detection callbacks, status reporting, cron expressions,
    job persistence, and execution history.
    """

    MAX_HISTORY_SIZE = 10  # Keep last N results per job

    def __init__(self):
        self._jobs: dict[str, ScheduleConfig] = {}
        self._statuses: dict[str, JobStatus] = {}
        self._callbacks: list[Callable[[str, Any], None]] = []
        self._running = False
        self._tasks: dict[str, asyncio.Task] = {}

    def add_job(self, config: ScheduleConfig) -> str:
        """Add a scheduled job. Returns job name."""
        name = config.name or config.url
        config.name = name
        self._jobs[name] = config
        self._statuses[name] = JobStatus(name=name, url=config.url)
        return name

    def remove_job(self, name: str) -> bool:
        """Remove a job by name. Returns True if found."""
        if name in self._jobs:
            del self._jobs[name]
            del self._statuses[name]
            if name in self._tasks:
                self._tasks[name].cancel()
                del self._tasks[name]
            return True
        return False

    def on_change(self, callback: Callable[[str, Any], None]) -> None:
        """Register a callback for when scrape results change."""
        self._callbacks.append(callback)

    def get_status(self, name: str) -> JobStatus | None:
        """Get status for a specific job."""
        return self._statuses.get(name)

    def get_all_status(self) -> SchedulerStatus:
        """Get overall scheduler status."""
        jobs = list(self._statuses.values())
        return SchedulerStatus(
            is_running=self._running,
            total_jobs=len(self._jobs),
            active_jobs=sum(1 for j in self._jobs.values() if j.enabled),
            total_runs=sum(j.run_count for j in jobs),
            total_errors=sum(j.error_count for j in jobs),
            jobs=jobs,
        )

    async def run_once(self, name: str, scrape_fn: Callable[[str], Awaitable[Any]]) -> Any:
        """Run a single scrape job immediately.

        Updates status tracking and job history. Calls change callbacks with result.
        """
        if name not in self._jobs:
            raise KeyError(f"Job not found: {name}")

        config = self._jobs[name]
        status = self._statuses[name]
        status.is_running = True

        timestamp = time.time()
        try:
            result = await scrape_fn(config.url)
            status.run_count += 1
            status.last_run = timestamp
            status.last_result = result
            status.is_running = False

            # Add to history
            self._add_history(name, timestamp, success=True, result=result)

            for cb in self._callbacks:
                try:
                    cb(name, result)
                except Exception:
                    logger.warning("Callback error for job %s", name)

            return result
        except Exception as e:
            status.error_count += 1
            status.last_error = str(e)
            status.is_running = False

            # Add error to history
            self._add_history(name, timestamp, success=False, error=str(e))
            raise

    async def start(self, scrape_fn: Callable[[str], Awaitable[Any]]) -> None:
        """Start the scheduler (run all enabled jobs on their intervals)."""
        self._running = True
        for name, config in self._jobs.items():
            if config.enabled:
                self._tasks[name] = asyncio.create_task(self._run_loop(name, config, scrape_fn))

    async def _run_loop(self, name: str, config: ScheduleConfig, scrape_fn: Callable[[str], Awaitable[Any]]) -> None:
        """Internal: run a job in a loop."""
        while self._running:
            try:
                await self.run_once(name, scrape_fn)
            except Exception:
                pass  # error already tracked in status
            self._statuses[name].next_run = time.time() + config.interval_seconds
            await asyncio.sleep(config.interval_seconds)

    def _add_history(self, name: str, timestamp: float, success: bool, result: Any = None, error: str | None = None) -> None:
        """Add an entry to job history, maintaining max size."""
        status = self._statuses.get(name)
        if not status:
            return

        entry = JobHistoryEntry(timestamp=timestamp, success=success, result=result, error=error)
        status.history.append(entry)

        # Trim history to max size
        if len(status.history) > self.MAX_HISTORY_SIZE:
            status.history = status.history[-self.MAX_HISTORY_SIZE :]

    def get_history(self, name: str, limit: int = 10) -> list[JobHistoryEntry]:
        """Get job execution history.

        Args:
            name: Job name
            limit: Maximum number of entries to return

        Returns:
            List of JobHistoryEntry, most recent first
        """
        status = self._statuses.get(name)
        if not status:
            return []

        return list(reversed(status.history[-limit:]))

    def save_jobs(self, file_path: str | Path) -> None:
        """Save job configurations to a JSON file.

        Args:
            file_path: Path to save the JSON file
        """
        path = Path(file_path)
        jobs_data = [asdict(config) for config in self._jobs.values()]

        with path.open("w") as f:
            json.dump(jobs_data, f, indent=2)

    def load_jobs(self, file_path: str | Path) -> int:
        """Load job configurations from a JSON file.

        Args:
            file_path: Path to load the JSON file from

        Returns:
            Number of jobs loaded
        """
        path = Path(file_path)
        if not path.exists():
            return 0

        with path.open("r") as f:
            jobs_data = json.load(f)

        count = 0
        for job_dict in jobs_data:
            config = ScheduleConfig(**job_dict)
            self.add_job(config)
            count += 1

        return count

    def apply_cron_interval(self, name: str) -> bool:
        """Apply cron expression to update job interval.

        Args:
            name: Job name

        Returns:
            True if cron was applied, False otherwise
        """
        config = self._jobs.get(name)
        if not config or not config.cron:
            return False

        interval = parse_cron(config.cron)
        if interval is None:
            logger.warning("Invalid cron expression for job %s: %s", name, config.cron)
            return False

        config.interval_seconds = interval
        return True

    def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        for task in self._tasks.values():
            task.cancel()
        self._tasks.clear()
