"""
Use Case 1: Tracker Enable
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional, Tuple

from src.client.exceptions import TemplateNotFoundError
from src.client.vmanage_client import VManageClient
from src.models.result_models import UCResult, UCStatus
from src.models.site_models import SiteConfig
from src.services.backup_service import BackupService
from src.services.diff_service import DiffService
from src.services.rollback_service import RollbackService
from src.services.state_service import StateService
from src.services.validation_service import ValidationService

logger = logging.getLogger("sdwan.uc1")

UC_KEY = "uc1"
UC_NAME = "Use Case 1: Tracker Enable"


class UC1TrackerEnable:
    def __init__(
        self,
        client: VManageClient,
        state: StateService,
        backup: BackupService,
        rollback: RollbackService,
        diff: DiffService,
        validation: ValidationService,
    ):
        self.client = client
        self.state = state
        self.backup = backup
        self.rollback = rollback
        self.diff = diff
        self.validation = validation

    def run(self, site: SiteConfig, dry_run: bool = False, force: bool = False) -> UCResult:
        device_template_id = site.get_device_template_id(UC_KEY)
        device_uuid = site.get_device_uuid(UC_KEY)
        result = UCResult(
            uc_key=UC_KEY,
            uc_name=UC_NAME,
            site_name=site.site_name,
            status=UCStatus.FAILED,
            template_id=device_template_id,
            device_uuid=device_uuid,
            dry_run=dry_run,
            force=force,
        )

        done, _ = self.state.is_done(site.site_name, UC_KEY)
        if done and not force:
            result.status = UCStatus.SKIPPED
            return result
        if force and done:
            self.state.clear(site.site_name, UC_KEY)

        result.warnings.extend(self.validation.validate_site_config(site, [UC_KEY]))

        if not any([site.tracker_template_id, site.tracker_template_name, site.nat_template_id, site.nat_template_name]):
            result.status = UCStatus.DRY_RUN if dry_run else UCStatus.SUCCESS
            result.diff_summary = "UC1 has no tracker/NAT template IDs or names in this lab workbook, so no change is required."
            return result

        backup_path: Optional[str] = None
        try:
            template_data = self.client.get_device_template(device_template_id)
            backup_path = self.backup.save(UC_KEY, device_template_id, template_data)
        except Exception as exc:
            logger.warning("Backup failed (continuing): %s", exc)
            template_data = self.client.get_device_template(device_template_id)

        result.before_config = self._get_config_preview(site)

        try:
            template_data, changed = self._attach_tracker_nat(site, template_data, persist=not dry_run)
        except Exception as exc:
            result.errors.append(str(exc))
            result.rollback_status = self.rollback.rollback(device_template_id, backup_path, str(exc))
            return result

        if dry_run:
            result.status = UCStatus.DRY_RUN
            result.diff_summary = "(dry-run - no changes deployed)"
            return result

        try:
            inputs = self.client.get_inputs(device_template_id, device_uuid)
            if not inputs:
                inputs = [{"csv-status": "completed", "csv-deviceId": device_uuid}]
            row = inputs[0]
            if site.tracker_src_ip:
                row["/0/0/vpn-instance/tracker-src-ip"] = site.tracker_src_ip
            row.update(site.variables)
            row["csv-status"] = "completed"
            result.variables_applied = {k: v for k, v in row.items() if not k.startswith("csv")}
            result.action_id = self.client.attach_and_deploy(device_template_id, inputs, is_edited=changed)
            poll_result = self.client.poll_task(result.action_id)
        except Exception as exc:
            result.errors.append(str(exc))
            result.rollback_status = self.rollback.rollback(device_template_id, backup_path, str(exc))
            return result

        result.after_config = self._get_config_preview(site)
        diff_files = self.diff.generate(result.before_config, result.after_config, f"{UC_KEY}_{site.site_name}")
        result.diff_summary = diff_files.get("diff_summary", "")
        return self._finalise(result, poll_result, site, backup_path)

    def _attach_tracker_nat(
        self,
        site: SiteConfig,
        template_data: Dict[str, Any],
        persist: bool = True,
    ) -> Tuple[Dict[str, Any], bool]:
        template_str = json.dumps(template_data)
        changed = False
        templates_to_attach = []
        if site.tracker_template_id or site.tracker_template_name:
            templates_to_attach.append((site.tracker_template_id, site.tracker_template_name, "cisco_tracker"))
        if site.nat_template_id or site.nat_template_name:
            templates_to_attach.append((site.nat_template_id, site.nat_template_name, "cisco_nat"))

        for template_id, template_name, template_type in templates_to_attach:
            tid = template_id or self._find_template_id(template_name, template_type)
            if tid in template_str:
                continue
            template_data["generalTemplates"].append(
                {"templateId": tid, "templateType": template_type, "subTemplates": []}
            )
            template_str = json.dumps(template_data)
            changed = True

        if changed and persist:
            self.client.update_device_template(site.get_device_template_id(UC_KEY), template_data)
        return template_data, changed

    def _find_template_id(self, name: str, template_type: str) -> str:
        templates = self.client.list_feature_templates(filter_type=template_type)
        for template in templates:
            if template.get("templateName", "").lower() == (name or "").lower():
                return template["templateId"]
        raise TemplateNotFoundError(template_name=name)

    def _get_config_preview(self, site: SiteConfig) -> str:
        try:
            device_template_id = site.get_device_template_id(UC_KEY)
            device_uuid = site.get_device_uuid(UC_KEY)
            inputs = self.client.get_inputs(device_template_id, device_uuid)
            if inputs:
                return self.client.get_config_preview(device_template_id, inputs[0])
        except Exception as exc:
            logger.info("Config preview unavailable; continuing without before/after diff capture")
        return ""

    def _finalise(self, result: UCResult, poll: Dict, site: SiteConfig, backup_path: Optional[str]) -> UCResult:
        device_template_id = site.get_device_template_id(UC_KEY)
        device_uuid = site.get_device_uuid(UC_KEY)
        if poll["status"] == "timeout":
            result.status = UCStatus.FAILED
            result.errors.append(f"Deploy timed out - action_id: {result.action_id}")
            result.rollback_status = self.rollback.rollback(device_template_id, backup_path, "deploy timeout")
        elif poll.get("soft"):
            result.status = UCStatus.SUCCESS
            self.state.mark_done(site.site_name, UC_KEY, device_template_id, device_uuid)
        elif poll["failure"] > 0:
            result.status = UCStatus.FAILED
            result.errors.append(f"Deploy failed on {poll['failure']} device(s)")
            result.rollback_status = self.rollback.rollback(device_template_id, backup_path, "device failure")
        else:
            result.status = UCStatus.SUCCESS
            self.state.mark_done(site.site_name, UC_KEY, device_template_id, device_uuid)
        return result
