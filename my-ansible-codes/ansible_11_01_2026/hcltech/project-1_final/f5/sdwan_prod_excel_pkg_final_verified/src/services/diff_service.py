"""
src/services/diff_service.py

Config diff service — generates human-readable before/after diffs
and saves them as text files and Excel reports.
"""

from __future__ import annotations

import difflib
import logging
import os
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger("sdwan.diff")


class DiffService:
    """Generates and persists before/after configuration diffs."""

    def __init__(self, reports_dir: str = "outputs"):
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)

    def generate(
        self,
        before: str,
        after: str,
        label: str = "config",
    ) -> Dict[str, str]:
        """
        Generate a unified diff between before and after configs.
        Saves before, after, and diff text files.
        Returns a dict of file paths.
        """
        ts     = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        prefix = os.path.join(self.reports_dir, f"{label}_{ts}")

        before_path = f"{prefix}_before.txt"
        after_path  = f"{prefix}_after.txt"
        diff_path   = f"{prefix}_diff.txt"

        _write(before_path, before or "# Not available\n")
        _write(after_path,  after or "# Not available\n")

        diff_lines = list(
            difflib.unified_diff(
                (before or "").splitlines(keepends=True),
                (after or "").splitlines(keepends=True),
                fromfile="before",
                tofile="after",
                lineterm="",
            )
        )
        diff_text = "".join(diff_lines) if diff_lines else "(no diff — configs identical or unavailable)"
        _write(diff_path, diff_text)

        logger.info(f"Diff files saved: {diff_path}")
        return {
            "before": before_path,
            "after":  after_path,
            "diff":   diff_path,
            "diff_summary": diff_text[:500] if diff_text else "",
        }

    def summary_lines(self, diff_text: str, max_lines: int = 30) -> str:
        """Return the first N lines of a diff for embedding in a report."""
        lines = diff_text.splitlines()
        if len(lines) <= max_lines:
            return diff_text
        return "\n".join(lines[:max_lines]) + f"\n... (+{len(lines) - max_lines} more lines)"


def _write(path: str, content: str) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as exc:
        logger.warning(f"Failed to write diff file {path}: {exc}")
