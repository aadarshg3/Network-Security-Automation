"""
src/services/backup_service.py

Template backup service — saves device template JSON before any modification.
Used by rollback_service to restore on failure.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from src.client.exceptions import BackupError

logger = logging.getLogger("sdwan.backup")


class BackupService:
    """Creates and loads template backups to/from the backup directory."""

    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)

    def save(
        self,
        label: str,
        template_id: str,
        template_data: Dict[str, Any],
    ) -> str:
        """
        Save a template JSON snapshot.
        Returns the full backup file path.
        """
        ts       = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{label}_{template_id[:8]}_{ts}.json"
        path     = os.path.join(self.backup_dir, filename)
        try:
            with open(path, "w") as f:
                json.dump(template_data, f, indent=2)
            logger.info(f"Backup saved: {path}")
            return path
        except OSError as exc:
            raise BackupError(f"Failed to save backup to {path}: {exc}") from exc

    def load(self, path: str) -> Dict[str, Any]:
        """Load a previously saved template backup JSON."""
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Backup file not found: {path}")
        with open(path, "r") as f:
            data = json.load(f)
        logger.info(f"Backup loaded: {path}")
        return data

    def latest_for(self, label: str, template_id: str) -> Optional[str]:
        """Return the most recent backup path matching a label+template_id prefix."""
        prefix = f"{label}_{template_id[:8]}_"
        candidates = [
            os.path.join(self.backup_dir, f)
            for f in os.listdir(self.backup_dir)
            if f.startswith(prefix) and f.endswith(".json")
        ]
        if not candidates:
            return None
        return sorted(candidates)[-1]
