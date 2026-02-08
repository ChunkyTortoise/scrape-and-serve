"""Change Detection with Diff Visualization: track page snapshots and visualize differences."""

from __future__ import annotations

import difflib
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class PageSnapshot:
    """A point-in-time capture of a page's content."""

    url: str
    content: str
    timestamp: datetime
    content_hash: str = ""

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()[:16]


@dataclass
class DiffResult:
    """Result of comparing two page snapshots."""

    url: str
    old_snapshot: PageSnapshot
    new_snapshot: PageSnapshot
    added_lines: list[str] = field(default_factory=list)
    removed_lines: list[str] = field(default_factory=list)
    changed_lines: int = 0
    similarity_ratio: float = 1.0


class DiffVisualizer:
    """Track page content over time and visualize changes between snapshots.

    Maintains an in-memory history of PageSnapshot objects per URL, with
    diff computation using stdlib difflib.
    """

    def __init__(self):
        self._history: dict[str, list[PageSnapshot]] = {}

    def add_snapshot(self, url: str, content: str, timestamp: datetime | None = None) -> PageSnapshot:
        """Add a new snapshot for a URL.

        Args:
            url: The page URL being tracked.
            content: The full text content of the page.
            timestamp: When the snapshot was taken (defaults to now UTC).

        Returns:
            The created PageSnapshot.
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        snapshot = PageSnapshot(url=url, content=content, timestamp=timestamp)

        if url not in self._history:
            self._history[url] = []
        self._history[url].append(snapshot)

        return snapshot

    def get_diff(self, url: str, index_a: int = -2, index_b: int = -1) -> DiffResult | None:
        """Compare two snapshots of a URL.

        Args:
            url: The page URL to compare.
            index_a: Index of the older snapshot (default: second-to-last).
            index_b: Index of the newer snapshot (default: last).

        Returns:
            DiffResult with change details, or None if fewer than 2 snapshots exist.
        """
        history = self._history.get(url, [])
        if len(history) < 2:
            return None

        try:
            old = history[index_a]
            new = history[index_b]
        except IndexError:
            return None

        old_lines = old.content.splitlines()
        new_lines = new.content.splitlines()

        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        similarity = matcher.ratio()

        added: list[str] = []
        removed: list[str] = []
        changed_count = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "insert":
                added.extend(new_lines[j1:j2])
                changed_count += j2 - j1
            elif tag == "delete":
                removed.extend(old_lines[i1:i2])
                changed_count += i2 - i1
            elif tag == "replace":
                removed.extend(old_lines[i1:i2])
                added.extend(new_lines[j1:j2])
                changed_count += max(i2 - i1, j2 - j1)

        return DiffResult(
            url=url,
            old_snapshot=old,
            new_snapshot=new,
            added_lines=added,
            removed_lines=removed,
            changed_lines=changed_count,
            similarity_ratio=round(similarity, 4),
        )

    def get_history(self, url: str) -> list[PageSnapshot]:
        """Get all snapshots for a URL, ordered chronologically."""
        return list(self._history.get(url, []))

    def get_unified_diff(self, url: str) -> str:
        """Get unified diff string for the latest two snapshots.

        Returns empty string if fewer than 2 snapshots exist.
        """
        history = self._history.get(url, [])
        if len(history) < 2:
            return ""

        old = history[-2]
        new = history[-1]

        old_lines = old.content.splitlines(keepends=True)
        new_lines = new.content.splitlines(keepends=True)

        diff_lines = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"{url} ({old.timestamp.isoformat()})",
            tofile=f"{url} ({new.timestamp.isoformat()})",
        )
        return "".join(diff_lines)

    def export_history(self, output_path: str) -> str:
        """Export all change history to JSON.

        Args:
            output_path: File path to write the JSON export.

        Returns:
            The output_path written to.
        """
        export: dict[str, list[dict]] = {}
        for url, snapshots in self._history.items():
            export[url] = [
                {
                    "url": s.url,
                    "content_hash": s.content_hash,
                    "timestamp": s.timestamp.isoformat(),
                    "content_length": len(s.content),
                }
                for s in snapshots
            ]

        with open(output_path, "w") as f:
            json.dump(export, f, indent=2)

        return output_path

    def get_change_summary(self) -> dict:
        """Summary of tracked URLs and changes.

        Returns:
            dict with keys: urls_tracked, total_snapshots, urls_with_changes
            (URLs where at least 2 snapshots have different content hashes).
        """
        urls_tracked = len(self._history)
        total_snapshots = sum(len(snaps) for snaps in self._history.values())

        urls_with_changes = 0
        for snapshots in self._history.values():
            if len(snapshots) >= 2:
                hashes = {s.content_hash for s in snapshots}
                if len(hashes) > 1:
                    urls_with_changes += 1

        return {
            "urls_tracked": urls_tracked,
            "total_snapshots": total_snapshots,
            "urls_with_changes": urls_with_changes,
        }
