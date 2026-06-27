"""
src/models/result_models.py

Typed result models for use case execution outcomes.
These feed directly into the Excel report generator.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class UCStatus(str, Enum):
    SUCCESS  = "success"
    SKIPPED  = "skipped"
    FAILED   = "failed"
    WARNING  = "warning"     # soft error — config landed but diff readback failed
    DRY_RUN  = "dry-run"
    ROLLED_BACK = "rolled-back"


@dataclass
class UCResult:
    """
    Result of a single use case execution.
    The uc_name field preserves the exact customer-provided use case name.
    """
    uc_key:       str              # internal key e.g. "uc1"
    uc_name:      str              # EXACT customer name e.g. "Use Case 1: Tracker Enable"
    site_name:    str
    status:       UCStatus
    timestamp:    datetime = field(default_factory=datetime.utcnow)
    template_id:  str = ""
    device_uuid:  str = ""
    action_id:    str = ""
    before_config: str = ""
    after_config:  str = ""
    diff_summary:  str = ""
    rollback_status: str = ""
    warnings:      List[str] = field(default_factory=list)
    errors:        List[str] = field(default_factory=list)
    variables_applied: Dict[str, Any] = field(default_factory=dict)
    dry_run:       bool = False
    force:         bool = False

    @property
    def is_success(self) -> bool:
        return self.status in (UCStatus.SUCCESS, UCStatus.WARNING, UCStatus.DRY_RUN)

    @property
    def display_status(self) -> str:
        """Human-readable status string for reports."""
        return self.status.value.upper()


@dataclass
class CutoverReport:
    """
    Aggregated report for a full site cutover run.
    Contains per-UC results and summary metadata.
    """
    site_name:    str
    run_at:       datetime = field(default_factory=datetime.utcnow)
    dry_run:      bool = False
    force:        bool = False
    results:      List[UCResult] = field(default_factory=list)
    profile_id:   str = ""
    region:       str = ""
    metallic_type: str = ""
    design_type:  Optional[str] = None

    def add(self, result: UCResult) -> None:
        self.results.append(result)

    @property
    def overall_status(self) -> str:
        statuses = {r.status for r in self.results}
        if UCStatus.FAILED in statuses:
            return "FAILED"
        if UCStatus.ROLLED_BACK in statuses:
            return "ROLLED_BACK"
        if UCStatus.WARNING in statuses:
            return "WARNING"
        if all(s == UCStatus.SKIPPED for s in statuses):
            return "SKIPPED"
        if UCStatus.DRY_RUN in statuses:
            return "DRY_RUN"
        return "SUCCESS"

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.is_success)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if r.status == UCStatus.FAILED)

    @property
    def skipped_count(self) -> int:
        return sum(1 for r in self.results if r.status == UCStatus.SKIPPED)
