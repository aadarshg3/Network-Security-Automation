"""
src/services/state_service.py

Idempotency tracker — records which use cases have been deployed per site.
State is persisted to JSON so re-runs skip already-completed work unless --force.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("sdwan.state")


class StateService:
    """
    Persistent idempotency tracker using a JSON file.

    State file structure:
    {
        "site1": {
            "uc1": {
                "deployed_at": "2025-01-01T12:00:00",
                "template_id": "...",
                "device_uuid": "...",
                "status": "success"
            },
            ...
        }
    }
    """

    def __init__(self, state_file: str = "sdwan_state.json"):
        self.state_file = state_file
        self._state: Dict[str, Any] = self._load()

    # ──────────────────────────────────────────────────────────────────────
    # Public Interface
    # ──────────────────────────────────────────────────────────────────────

    def is_done(self, site_name: str, uc_key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if a use case has already been deployed for a site.
        Returns (is_done: bool, record: dict).
        """
        record = self._state.get(site_name, {}).get(uc_key, {})
        if record.get("status") in ("success", "warning"):
            logger.info(
                f"State: {site_name}.{uc_key} already deployed at "
                f"{record.get('deployed_at')} — idempotency skip"
            )
            return True, record
        return False, {}

    def mark_done(
        self,
        site_name: str,
        uc_key: str,
        template_id: str,
        device_uuid: str,
        status: str = "success",
    ) -> None:
        """Record a successful deployment in the state file."""
        self._state.setdefault(site_name, {})[uc_key] = {
            "deployed_at":  datetime.utcnow().isoformat(),
            "template_id":  template_id,
            "device_uuid":  device_uuid,
            "status":       status,
        }
        self._save()
        logger.info(f"State saved: {site_name}.{uc_key} = {status}")

    def clear(self, site_name: str, uc_key: Optional[str] = None) -> None:
        """Clear state for a site (or a specific UC) — called by --force."""
        if uc_key:
            self._state.get(site_name, {}).pop(uc_key, None)
            logger.info(f"State cleared: {site_name}.{uc_key}")
        else:
            self._state.pop(site_name, None)
            logger.info(f"State cleared: all UCs for {site_name}")
        self._save()

    def show_all(self) -> None:
        """Print the current state to stdout."""
        if not self._state:
            print("  No deployments recorded yet.")
            return
        for site, ucs in self._state.items():
            print(f"  Site: {site}")
            for uc, rec in ucs.items():
                print(
                    f"    {uc}: {rec.get('status', 'unknown')}"
                    f" at {rec.get('deployed_at', 'N/A')}"
                )

    def get_site_state(self, site_name: str) -> Dict[str, Any]:
        """Return the full state dict for a given site."""
        return self._state.get(site_name, {})

    # ──────────────────────────────────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────────────────────────────────

    def _load(self) -> Dict[str, Any]:
        if os.path.isfile(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                logger.debug(f"State loaded from {self.state_file}")
                return data
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning(f"Failed to load state file ({exc}) — starting fresh")
        return {}

    def _save(self) -> None:
        try:
            with open(self.state_file, "w") as f:
                json.dump(self._state, f, indent=2)
        except OSError as exc:
            logger.error(f"Failed to save state file: {exc}")
