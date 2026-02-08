"""Scheduled scraping: asyncio-based scheduling with status tracking and callbacks."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

logger = logging.getLogger("scrape_and_serve.scheduler")


@dataclass
class ScheduleConfig:
    """Configuration for a scheduled scrape job."""

    url: str
    interval_seconds: int = 3600  # default: hourly
    name: str = ""
    enabled: bool = True


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


@dataclass
class SchedulerStatus:
    """Overall scheduler status."""

    is_running: bool
    total_jobs: int
    active_jobs: int
    total_runs: int
    total_errors: int
    jobs: list[JobStatus] = field(default_factory=list)


class ScrapeScheduler:
    """Asyncio-based scrape scheduler with status tracking.

    Manages multiple scheduled scrape jobs with error tracking,
    change detection callbacks, and status reporting.
    """

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

        Updates status tracking. Calls change callbacks with result.
        """
        if name not in self._jobs:
            raise KeyError(f"Job not found: {name}")

        config = self._jobs[name]
        status = self._statuses[name]
        status.is_running = True

        try:
            result = await scrape_fn(config.url)
            status.run_count += 1
            status.last_run = time.time()
            status.last_result = result
            status.is_running = False

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

    def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        for task in self._tasks.values():
            task.cancel()
        self._tasks.clear()
