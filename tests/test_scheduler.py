"""Tests for the scheduler module."""

import asyncio

import pytest

from scrape_and_serve.scheduler import ScheduleConfig, ScrapeScheduler


async def mock_scrape(url: str) -> str:
    """Test helper: simulate a successful scrape."""
    return f"content from {url}"


async def failing_scrape(url: str) -> str:
    """Test helper: simulate a failing scrape."""
    raise RuntimeError("Network error")


class TestJobManagement:
    def test_add_job(self):
        scheduler = ScrapeScheduler()
        name = scheduler.add_job(ScheduleConfig(url="https://example.com", name="example"))
        assert name == "example"
        status = scheduler.get_all_status()
        assert status.total_jobs == 1

    def test_add_job_auto_name(self):
        scheduler = ScrapeScheduler()
        name = scheduler.add_job(ScheduleConfig(url="https://example.com"))
        assert name == "https://example.com"

    def test_remove_job(self):
        scheduler = ScrapeScheduler()
        scheduler.add_job(ScheduleConfig(url="https://example.com", name="example"))
        assert scheduler.remove_job("example") is True
        assert scheduler.get_all_status().total_jobs == 0

    def test_remove_nonexistent(self):
        scheduler = ScrapeScheduler()
        assert scheduler.remove_job("does_not_exist") is False


class TestRunOnce:
    @pytest.mark.asyncio
    async def test_run_once_success(self):
        scheduler = ScrapeScheduler()
        scheduler.add_job(ScheduleConfig(url="https://example.com", name="test"))
        result = await scheduler.run_once("test", mock_scrape)
        assert result == "content from https://example.com"
        status = scheduler.get_status("test")
        assert status is not None
        assert status.run_count == 1
        assert status.last_run is not None
        assert status.is_running is False

    @pytest.mark.asyncio
    async def test_run_once_error(self):
        scheduler = ScrapeScheduler()
        scheduler.add_job(ScheduleConfig(url="https://example.com", name="test"))
        with pytest.raises(RuntimeError, match="Network error"):
            await scheduler.run_once("test", failing_scrape)
        status = scheduler.get_status("test")
        assert status is not None
        assert status.error_count == 1
        assert status.last_error == "Network error"
        assert status.is_running is False

    @pytest.mark.asyncio
    async def test_run_once_callback(self):
        scheduler = ScrapeScheduler()
        scheduler.add_job(ScheduleConfig(url="https://example.com", name="test"))
        results: list[tuple[str, str]] = []
        scheduler.on_change(lambda name, result: results.append((name, result)))
        await scheduler.run_once("test", mock_scrape)
        assert len(results) == 1
        assert results[0] == ("test", "content from https://example.com")

    @pytest.mark.asyncio
    async def test_run_once_nonexistent(self):
        scheduler = ScrapeScheduler()
        with pytest.raises(KeyError, match="Job not found"):
            await scheduler.run_once("nonexistent", mock_scrape)


class TestStatus:
    def test_initial_status(self):
        scheduler = ScrapeScheduler()
        status = scheduler.get_all_status()
        assert status.is_running is False
        assert status.total_jobs == 0
        assert status.active_jobs == 0
        assert status.total_runs == 0
        assert status.total_errors == 0
        assert status.jobs == []

    def test_status_after_add(self):
        scheduler = ScrapeScheduler()
        scheduler.add_job(ScheduleConfig(url="https://a.com", name="a"))
        scheduler.add_job(ScheduleConfig(url="https://b.com", name="b"))
        status = scheduler.get_all_status()
        assert status.total_jobs == 2
        assert status.active_jobs == 2

    def test_job_status(self):
        scheduler = ScrapeScheduler()
        scheduler.add_job(ScheduleConfig(url="https://example.com", name="test"))
        status = scheduler.get_status("test")
        assert status is not None
        assert status.name == "test"
        assert status.url == "https://example.com"
        assert status.run_count == 0
        assert status.is_running is False


class TestSchedulerControl:
    def test_stop(self):
        scheduler = ScrapeScheduler()
        scheduler._running = True
        scheduler.stop()
        assert scheduler._running is False

    @pytest.mark.asyncio
    async def test_start_and_stop(self):
        scheduler = ScrapeScheduler()
        scheduler.add_job(ScheduleConfig(url="https://example.com", name="test", interval_seconds=1))
        await scheduler.start(mock_scrape)
        assert scheduler._running is True
        # Give the loop a moment to run at least once
        await asyncio.sleep(0.05)
        scheduler.stop()
        assert scheduler._running is False

    def test_disabled_job(self):
        scheduler = ScrapeScheduler()
        scheduler.add_job(ScheduleConfig(url="https://example.com", name="disabled", enabled=False))
        status = scheduler.get_all_status()
        assert status.total_jobs == 1
        assert status.active_jobs == 0


class TestMultipleCallbacks:
    """Tests for callback behavior with multiple or failing callbacks."""

    @pytest.mark.asyncio
    async def test_multiple_callbacks_all_called(self):
        scheduler = ScrapeScheduler()
        scheduler.add_job(ScheduleConfig(url="https://example.com", name="test"))
        calls_a: list[str] = []
        calls_b: list[str] = []
        scheduler.on_change(lambda name, result: calls_a.append(name))
        scheduler.on_change(lambda name, result: calls_b.append(name))
        await scheduler.run_once("test", mock_scrape)
        assert len(calls_a) == 1
        assert len(calls_b) == 1

    @pytest.mark.asyncio
    async def test_callback_error_does_not_stop_result(self):
        scheduler = ScrapeScheduler()
        scheduler.add_job(ScheduleConfig(url="https://example.com", name="test"))

        def bad_callback(name: str, result: object) -> None:
            raise ValueError("callback boom")

        results: list[str] = []
        scheduler.on_change(bad_callback)
        scheduler.on_change(lambda name, result: results.append(name))
        result = await scheduler.run_once("test", mock_scrape)
        # First callback fails, but run_once still returns and second callback fires
        assert result == "content from https://example.com"
        assert len(results) == 1


class TestRunOnceExtended:
    """Extended run_once tests covering status fields."""

    @pytest.mark.asyncio
    async def test_last_result_stored(self):
        scheduler = ScrapeScheduler()
        scheduler.add_job(ScheduleConfig(url="https://example.com", name="test"))
        await scheduler.run_once("test", mock_scrape)
        status = scheduler.get_status("test")
        assert status is not None
        assert status.last_result == "content from https://example.com"

    @pytest.mark.asyncio
    async def test_run_count_increments_on_multiple_runs(self):
        scheduler = ScrapeScheduler()
        scheduler.add_job(ScheduleConfig(url="https://example.com", name="test"))
        await scheduler.run_once("test", mock_scrape)
        await scheduler.run_once("test", mock_scrape)
        await scheduler.run_once("test", mock_scrape)
        status = scheduler.get_status("test")
        assert status is not None
        assert status.run_count == 3

    @pytest.mark.asyncio
    async def test_error_count_increments_on_multiple_errors(self):
        scheduler = ScrapeScheduler()
        scheduler.add_job(ScheduleConfig(url="https://example.com", name="test"))
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await scheduler.run_once("test", failing_scrape)
        status = scheduler.get_status("test")
        assert status is not None
        assert status.error_count == 3

    @pytest.mark.asyncio
    async def test_remove_job_after_run(self):
        scheduler = ScrapeScheduler()
        scheduler.add_job(ScheduleConfig(url="https://example.com", name="test"))
        await scheduler.run_once("test", mock_scrape)
        assert scheduler.remove_job("test") is True
        assert scheduler.get_status("test") is None


class TestStatusExtended:
    """Extended status tests for edge cases and aggregate counters."""

    def test_get_status_nonexistent_returns_none(self):
        scheduler = ScrapeScheduler()
        assert scheduler.get_status("nonexistent") is None

    @pytest.mark.asyncio
    async def test_aggregate_total_runs(self):
        scheduler = ScrapeScheduler()
        scheduler.add_job(ScheduleConfig(url="https://a.com", name="a"))
        scheduler.add_job(ScheduleConfig(url="https://b.com", name="b"))
        await scheduler.run_once("a", mock_scrape)
        await scheduler.run_once("a", mock_scrape)
        await scheduler.run_once("b", mock_scrape)
        status = scheduler.get_all_status()
        assert status.total_runs == 3

    @pytest.mark.asyncio
    async def test_aggregate_total_errors(self):
        scheduler = ScrapeScheduler()
        scheduler.add_job(ScheduleConfig(url="https://a.com", name="a"))
        scheduler.add_job(ScheduleConfig(url="https://b.com", name="b"))
        with pytest.raises(RuntimeError):
            await scheduler.run_once("a", failing_scrape)
        with pytest.raises(RuntimeError):
            await scheduler.run_once("b", failing_scrape)
        status = scheduler.get_all_status()
        assert status.total_errors == 2

    def test_multiple_jobs_mixed_enabled(self):
        scheduler = ScrapeScheduler()
        scheduler.add_job(ScheduleConfig(url="https://a.com", name="a", enabled=True))
        scheduler.add_job(ScheduleConfig(url="https://b.com", name="b", enabled=False))
        scheduler.add_job(ScheduleConfig(url="https://c.com", name="c", enabled=True))
        status = scheduler.get_all_status()
        assert status.total_jobs == 3
        assert status.active_jobs == 2
        assert len(status.jobs) == 3

    def test_job_interval_stored(self):
        scheduler = ScrapeScheduler()
        scheduler.add_job(ScheduleConfig(url="https://example.com", name="hourly", interval_seconds=7200))
        config = scheduler._jobs["hourly"]
        assert config.interval_seconds == 7200


class TestSchedulerLifecycle:
    """Tests for start/stop lifecycle edge cases."""

    @pytest.mark.asyncio
    async def test_stop_clears_tasks(self):
        scheduler = ScrapeScheduler()
        scheduler.add_job(ScheduleConfig(url="https://example.com", name="test", interval_seconds=1))
        await scheduler.start(mock_scrape)
        await asyncio.sleep(0.05)
        scheduler.stop()
        assert len(scheduler._tasks) == 0

    @pytest.mark.asyncio
    async def test_disabled_job_not_started_as_task(self):
        scheduler = ScrapeScheduler()
        scheduler.add_job(ScheduleConfig(url="https://a.com", name="active", interval_seconds=1))
        scheduler.add_job(ScheduleConfig(url="https://b.com", name="disabled", enabled=False, interval_seconds=1))
        await scheduler.start(mock_scrape)
        await asyncio.sleep(0.05)
        assert "active" in scheduler._tasks
        assert "disabled" not in scheduler._tasks
        scheduler.stop()
