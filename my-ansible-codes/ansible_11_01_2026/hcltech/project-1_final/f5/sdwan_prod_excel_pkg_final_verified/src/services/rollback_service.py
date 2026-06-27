"""
src/services/rollback_service.py

Safe auto-rollback service.
On any deployment failure, restores the device template from the pre-change backup.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from src.client.vmanage_client import VManageClient
from src.client.exceptions import RollbackError
from src.services.backup_service import BackupService

logger = logging.getLogger("sdwan.rollback")


class RollbackService:
    """Restores device templates from backup on deployment failure."""

    def __init__(self, client: VManageClient, backup_service: BackupService):
        self.client  = client
        self.backups = backup_service

    def rollback(
        self,
        template_id: str,
        backup_path: Optional[str],
        reason: str,
    ) -> str:
        """
        Restore a device template from a backup file.

        Args:
            template_id:  The vManage device template ID to restore.
            backup_path:  Full path to the backup JSON file.
            reason:       Human-readable reason for triggering rollback.

        Returns:
            Status string: "success" | "no_backup" | "failed"
        """
        logger.warning(f"ROLLBACK TRIGGERED — reason: {reason}")
        logger.warning(f"  template_id : {template_id[:16]}...")
        logger.warning(f"  backup_path : {backup_path}")

        if not backup_path:
            msg = "No backup available — manual restore required via vManage UI"
            logger.error(msg)
            return "no_backup"

        try:
            backup_data = self.backups.load(backup_path)
        except FileNotFoundError as exc:
            logger.error(f"Backup file missing: {exc}")
            return "no_backup"

        logger.info("Restoring template from backup via PUT...")
        try:
            self.client.rollback_device_template(template_id, backup_data)
            logger.info("ROLLBACK SUCCESSFUL")
            return "success"
        except Exception as exc:
            error_msg = (
                f"ROLLBACK FAILED: {exc}\n"
                f"Manual restore required — backup file: {backup_path}"
            )
            logger.error(error_msg)
            raise RollbackError(error_msg) from exc
