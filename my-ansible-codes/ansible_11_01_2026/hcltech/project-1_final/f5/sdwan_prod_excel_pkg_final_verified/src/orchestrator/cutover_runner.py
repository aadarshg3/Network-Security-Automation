"""
src/orchestrator/cutover_runner.py

Cutover orchestrator — wires all services and use cases together.
Responsible for:
  - Loading site config and resolving category profile
  - Running selected use cases in sequence
  - Collecting and returning a CutoverReport
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import yaml

from src.client.vmanage_client import VManageClient
from src.models.result_models import CutoverReport, UCResult, UCStatus
from src.models.site_models import SiteConfig
from src.services.backup_service import BackupService
from src.services.diff_service import DiffService
from src.services.profile_service import ProfileService
from src.services.report_service import ReportService
from src.services.rollback_service import RollbackService
from src.services.state_service import StateService
from src.services.validation_service import ValidationService
from src.usecases.uc1_tracker_enable import UC1TrackerEnable
from src.usecases.uc2_sig_template import UC2SIGTemplate
from src.usecases.uc3_create_a_firewall_transit_interface import UC3CreateAFirewallTransitInterface
from src.usecases.uc4_create_a_firewall_transit_interface import UC4CreateAFirewallTransitInterface

logger = logging.getLogger("sdwan.orchestrator")

# Ordered run sequence
UC_ORDER = ["uc1", "uc2", "uc3", "uc4"]


class CutoverRunner:
    """
    Orchestrates a full or partial SD-WAN site cutover.
    Resolves site profile, instantiates services, runs selected UCs,
    and produces an Excel report.
    """

    def __init__(
        self,
        settings: Dict[str, Any],
        profiles_config: Dict[str, Any],
    ):
        self.settings         = settings
        self.profile_service  = ProfileService(profiles_config)
        self.sites_config     = profiles_config.get("sites", {})
        self._client: Optional[VManageClient] = None

    # ──────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────

    def run(
        self,
        site_name: str,
        uc_keys: List[str],
        password: str,
        dry_run: bool = False,
        force: bool = False,
        report_dir: str = "outputs",
        site_override: Optional[SiteConfig] = None,
        profile_override=None,
    ) -> CutoverReport:
        """
        Execute the requested use cases for a site.
        Returns a CutoverReport with per-UC results.
        """
        site = site_override or self._load_site(site_name)
        profile = profile_override or self.profile_service.resolve(
            site.region, site.metallic_type, site.design_type
        )

        # Filter uc_keys to only those enabled for this profile
        enabled = profile.enabled_use_cases
        requested_and_enabled = [k for k in UC_ORDER if k in uc_keys and k in enabled]
        skipped_by_profile    = [k for k in uc_keys if k not in enabled]

        if skipped_by_profile:
            logger.warning(
                f"Profile '{profile.profile_id}' disables: {skipped_by_profile} "
                f"— these will be skipped"
            )

        report = CutoverReport(
            site_name=site_name,
            dry_run=dry_run,
            force=force,
            profile_id=profile.profile_id,
            region=site.region,
            metallic_type=site.metallic_type,
            design_type=site.design_type,
        )

        # Add skipped-by-profile results
        for k in skipped_by_profile:
            from src.usecases.uc1_tracker_enable import UC_NAME as UC1_NAME
            from src.usecases.uc2_sig_template import UC_NAME as UC2_NAME
            from src.usecases.uc3_create_a_firewall_transit_interface import UC_NAME as UC3_NAME
            from src.usecases.uc4_create_a_firewall_transit_interface import UC_NAME as UC4_NAME
            names = {"uc1": UC1_NAME, "uc2": UC2_NAME, "uc3": UC3_NAME, "uc4": UC4_NAME}
            report.add(UCResult(
                uc_key=k, uc_name=names.get(k, k),
                site_name=site_name,
                status=UCStatus.SKIPPED,
                warnings=[f"Skipped by profile '{profile.profile_id}' — not enabled for this region/metallic"],
            ))

        if not requested_and_enabled:
            logger.warning("No enabled use cases to run")
            return report

        # ── Build shared services ─────────────────────────────
        paths       = self.settings.get("paths", {})
        state_svc   = StateService(state_file=paths.get("state_file", "sdwan_state.json"))
        backup_svc  = BackupService(backup_dir=paths.get("backups_dir", "backups"))
        diff_svc    = DiffService(reports_dir=report_dir)
        validation  = ValidationService(profile=profile)

        # ── Login ─────────────────────────────────────────────
        vm_cfg      = self.settings.get("vmanage", {})
        self._client = VManageClient(
            host=vm_cfg.get("host", ""),
            verify_ssl=vm_cfg.get("verify_ssl", False),
            timeout=vm_cfg.get("timeout_seconds", 30),
            retry_attempts=vm_cfg.get("retry_attempts", 3),
            retry_delay=vm_cfg.get("retry_delay_seconds", 5.0),
            poll_timeout=vm_cfg.get("poll_timeout_seconds", 180),
            poll_interval=vm_cfg.get("poll_interval_seconds", 5),
            soft_error_patterns=self.settings.get("soft_error_patterns"),
        )
        self._client.login(vm_cfg.get("username", "admin"), password)

        rollback_svc = RollbackService(self._client, backup_svc)

        # ── Instantiate UCs ───────────────────────────────────
        uc_instances = {
            "uc1": UC1TrackerEnable(self._client, state_svc, backup_svc, rollback_svc, diff_svc, validation),
            "uc2": UC2SIGTemplate(self._client, state_svc, backup_svc, rollback_svc, diff_svc, validation),
            "uc3": UC3CreateAFirewallTransitInterface(self._client, state_svc, backup_svc, rollback_svc, diff_svc, validation),
            "uc4": UC4CreateAFirewallTransitInterface(self._client, state_svc, backup_svc, rollback_svc, diff_svc, validation),
        }

        # ── Run selected UCs in order ─────────────────────────
        try:
            for uc_key in requested_and_enabled:
                logger.info(f"\nRunning {uc_key.upper()} for site '{site_name}'")
                uc = uc_instances[uc_key]
                result = uc.run(site=site, dry_run=dry_run, force=force)
                report.add(result)

                # Stop on hard failure unless dry-run
                if result.status == UCStatus.FAILED and not dry_run:
                    logger.error(
                        f"{uc_key.upper()} FAILED — stopping cutover for site '{site_name}'"
                    )
                    break
        finally:
            try:
                self._client.logout()
            except Exception:
                pass

        # ── Generate report ───────────────────────────────────
        report_svc  = ReportService(reports_dir=report_dir)
        report_path = report_svc.generate(report)
        logger.info(f"\nReport saved: {report_path}")

        return report

    # ──────────────────────────────────────────────────────────────────────
    # Internal
    # ──────────────────────────────────────────────────────────────────────

    def _load_site(self, site_name: str) -> SiteConfig:
        raw = self.sites_config.get(site_name)
        if not raw:
            raise ValueError(
                f"Site '{site_name}' not found in site_profiles.yaml. "
                f"Available: {list(self.sites_config.keys())}"
            )
        return SiteConfig.from_dict(raw)
