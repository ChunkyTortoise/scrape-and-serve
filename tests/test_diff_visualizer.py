"""Tests for the diff visualizer module."""

import json
import os
from datetime import datetime, timezone

from scrape_and_serve.diff_visualizer import DiffVisualizer, PageSnapshot


class TestPageSnapshot:
    def test_auto_hash(self):
        snap = PageSnapshot(url="https://example.com", content="hello", timestamp=datetime.now(timezone.utc))
        assert len(snap.content_hash) == 16
        assert snap.content_hash != ""

    def test_consistent_hash(self):
        ts = datetime(2025, 1, 1, tzinfo=timezone.utc)
        s1 = PageSnapshot(url="https://a.com", content="same content", timestamp=ts)
        s2 = PageSnapshot(url="https://a.com", content="same content", timestamp=ts)
        assert s1.content_hash == s2.content_hash

    def test_different_content_different_hash(self):
        ts = datetime(2025, 1, 1, tzinfo=timezone.utc)
        s1 = PageSnapshot(url="https://a.com", content="version 1", timestamp=ts)
        s2 = PageSnapshot(url="https://a.com", content="version 2", timestamp=ts)
        assert s1.content_hash != s2.content_hash


class TestAddAndRetrieve:
    def test_add_snapshot_and_retrieve(self):
        viz = DiffVisualizer()
        snap = viz.add_snapshot("https://example.com", "Hello World")
        assert snap.url == "https://example.com"
        assert snap.content == "Hello World"
        assert snap.content_hash != ""

        history = viz.get_history("https://example.com")
        assert len(history) == 1
        assert history[0].content == "Hello World"

    def test_empty_history_for_unknown_url(self):
        viz = DiffVisualizer()
        assert viz.get_history("https://unknown.com") == []


class TestDiffDetection:
    def test_detects_changes_between_snapshots(self):
        viz = DiffVisualizer()
        viz.add_snapshot("https://shop.com", "Price: $10\nStock: 50")
        viz.add_snapshot("https://shop.com", "Price: $15\nStock: 50\nNew item available")

        diff = viz.get_diff("https://shop.com")
        assert diff is not None
        assert diff.url == "https://shop.com"
        assert len(diff.added_lines) > 0
        assert diff.changed_lines > 0
        assert diff.similarity_ratio < 1.0

    def test_no_diff_with_single_snapshot(self):
        viz = DiffVisualizer()
        viz.add_snapshot("https://single.com", "only one")
        assert viz.get_diff("https://single.com") is None

    def test_identical_content_shows_no_changes(self):
        viz = DiffVisualizer()
        viz.add_snapshot("https://static.com", "same content\nline two")
        viz.add_snapshot("https://static.com", "same content\nline two")

        diff = viz.get_diff("https://static.com")
        assert diff is not None
        assert diff.added_lines == []
        assert diff.removed_lines == []
        assert diff.changed_lines == 0
        assert diff.similarity_ratio == 1.0

    def test_removed_lines_detected(self):
        viz = DiffVisualizer()
        viz.add_snapshot("https://page.com", "line 1\nline 2\nline 3")
        viz.add_snapshot("https://page.com", "line 1\nline 3")

        diff = viz.get_diff("https://page.com")
        assert diff is not None
        assert "line 2" in diff.removed_lines


class TestMultipleUrls:
    def test_urls_tracked_independently(self):
        viz = DiffVisualizer()
        viz.add_snapshot("https://a.com", "content A v1")
        viz.add_snapshot("https://a.com", "content A v2")
        viz.add_snapshot("https://b.com", "content B v1")

        assert len(viz.get_history("https://a.com")) == 2
        assert len(viz.get_history("https://b.com")) == 1

        # a.com has a diff, b.com does not
        assert viz.get_diff("https://a.com") is not None
        assert viz.get_diff("https://b.com") is None


class TestUnifiedDiff:
    def test_unified_diff_format(self):
        viz = DiffVisualizer()
        viz.add_snapshot("https://doc.com", "line 1\nline 2")
        viz.add_snapshot("https://doc.com", "line 1\nline 2 modified\nline 3")

        udiff = viz.get_unified_diff("https://doc.com")
        assert "---" in udiff
        assert "+++" in udiff
        assert "doc.com" in udiff

    def test_unified_diff_empty_with_one_snapshot(self):
        viz = DiffVisualizer()
        viz.add_snapshot("https://one.com", "only one snapshot")
        assert viz.get_unified_diff("https://one.com") == ""


class TestExportHistory:
    def test_export_to_json(self, tmp_path):
        viz = DiffVisualizer()
        viz.add_snapshot("https://export.com", "v1", datetime(2025, 1, 1, tzinfo=timezone.utc))
        viz.add_snapshot("https://export.com", "v2", datetime(2025, 1, 2, tzinfo=timezone.utc))

        output = str(tmp_path / "history.json")
        result_path = viz.export_history(output)
        assert result_path == output
        assert os.path.exists(output)

        with open(output) as f:
            data = json.load(f)
        assert "https://export.com" in data
        assert len(data["https://export.com"]) == 2
        assert data["https://export.com"][0]["content_length"] == 2


class TestChangeSummary:
    def test_summary_stats(self):
        viz = DiffVisualizer()
        viz.add_snapshot("https://changed.com", "v1")
        viz.add_snapshot("https://changed.com", "v2")
        viz.add_snapshot("https://stable.com", "same")
        viz.add_snapshot("https://stable.com", "same")

        summary = viz.get_change_summary()
        assert summary["urls_tracked"] == 2
        assert summary["total_snapshots"] == 4
        assert summary["urls_with_changes"] == 1  # only changed.com has different hashes

    def test_empty_summary(self):
        viz = DiffVisualizer()
        summary = viz.get_change_summary()
        assert summary["urls_tracked"] == 0
        assert summary["total_snapshots"] == 0
        assert summary["urls_with_changes"] == 0
