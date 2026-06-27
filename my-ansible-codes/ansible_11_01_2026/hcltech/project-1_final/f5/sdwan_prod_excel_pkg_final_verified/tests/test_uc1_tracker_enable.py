"""
tests/test_uc1_tracker_enable.py

Unit tests for Use Case 1: Tracker Enable

Tests:
  - Successful deployment
  - Idempotency: skip if already deployed
  - --force re-run clears state and re-deploys
  - Dry-run: no deployment
  - Soft error handling (config diff warning = warning, not failure)
  - Rollback triggered on deploy failure
  - Template already attached → skipped without change
"""

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime

from src.models.result_models import UCStatus
from src.services.backup_service import BackupService
from src.services.diff_service import DiffService
from src.services.rollback_service import RollbackService
from src.services.state_service import StateService
from src.services.validation_service import ValidationService
from src.usecases.uc1_tracker_enable import UC1TrackerEnable

from tests.mock_data import (
    make_site, make_mock_client, make_device_template,
    make_feature_templates, poll_success, poll_failure,
    poll_soft_error, poll_timeout,
)


def _make_uc1(client=None, state=None):
    """Build a UC1TrackerEnable instance with mocked services."""
    client  = client or make_mock_client()
    state   = state or MagicMock(spec=StateService)
    state.is_done.return_value = (False, {})
    backup  = MagicMock(spec=BackupService)
    backup.save.return_value   = "/tmp/backup_uc1_test.json"
    rollback = MagicMock(spec=RollbackService)
    rollback.rollback.return_value = "success"
    diff    = MagicMock(spec=DiffService)
    diff.generate.return_value = {"diff_summary": "--- before\n+++ after\n"}
    validation = ValidationService()
    return UC1TrackerEnable(client, state, backup, rollback, diff, validation)


class TestUC1Idempotency:

    def test_skip_if_already_deployed(self):
        state = MagicMock(spec=StateService)
        state.is_done.return_value = (True, {"deployed_at": "2025-01-01T12:00:00", "status": "success"})
        uc1   = _make_uc1(state=state)
        site  = make_site()

        result = uc1.run(site, dry_run=False, force=False)

        assert result.status == UCStatus.SKIPPED
        uc1.client.attach_and_deploy.assert_not_called()

    def test_force_reruns_even_if_deployed(self):
        state = MagicMock(spec=StateService)
        state.is_done.return_value = (True, {"deployed_at": "2025-01-01T12:00:00"})
        client = make_mock_client(
            feature_templates=make_feature_templates([
                ("cisco-tracker-template", "cisco_tracker", "tracker-tid-001"),
                ("cisco-nat-template",     "cisco_nat",     "nat-tid-001"),
            ])
        )
        uc1 = _make_uc1(client=client, state=state)
        site = make_site()

        result = uc1.run(site, dry_run=False, force=True)

        state.clear.assert_called_once_with(site.site_name, "uc1")
        assert result.status == UCStatus.SUCCESS


class TestUC1DryRun:

    def test_dry_run_does_not_deploy(self):
        uc1  = _make_uc1()
        site = make_site()

        result = uc1.run(site, dry_run=True, force=False)

        assert result.status == UCStatus.DRY_RUN
        uc1.client.attach_and_deploy.assert_not_called()
        uc1.state.mark_done.assert_not_called()


class TestUC1Success:

    def test_successful_deploy(self):
        client = make_mock_client(
            feature_templates=make_feature_templates([
                ("cisco-tracker-template", "cisco_tracker", "tracker-tid-001"),
                ("cisco-nat-template",     "cisco_nat",     "nat-tid-001"),
            ]),
            poll_result=poll_success(),
        )
        uc1  = _make_uc1(client=client)
        site = make_site()

        result = uc1.run(site, dry_run=False, force=False)

        assert result.status == UCStatus.SUCCESS
        uc1.state.mark_done.assert_called_once()

    def test_tracker_already_attached_not_changed(self):
        """If tracker template is already in device template, no PUT should be called."""
        template = make_device_template()
        template["generalTemplates"].append({
            "templateId":   "tracker-tid-001",
            "templateType": "cisco_tracker",
            "subTemplates": [],
        })
        template["generalTemplates"].append({
            "templateId":   "nat-tid-001",
            "templateType": "cisco_nat",
            "subTemplates": [],
        })
        client = make_mock_client(
            template=template,
            feature_templates=make_feature_templates([
                ("cisco-tracker-template", "cisco_tracker", "tracker-tid-001"),
                ("cisco-nat-template",     "cisco_nat",     "nat-tid-001"),
            ]),
            poll_result=poll_success(),
        )
        uc1  = _make_uc1(client=client)
        site = make_site()

        uc1.run(site, dry_run=False, force=False)

        # Template was not modified — PUT should not have been called
        client.update_device_template.assert_not_called()


class TestUC1SoftError:

    def test_soft_error_treated_as_warning_not_failure(self):
        client = make_mock_client(
            feature_templates=make_feature_templates([
                ("cisco-tracker-template", "cisco_tracker", "tracker-tid-001"),
            ]),
            poll_result=poll_soft_error(),
        )
        uc1  = _make_uc1(client=client)
        site = make_site()

        result = uc1.run(site, dry_run=False, force=False)

        assert result.status == UCStatus.WARNING
        assert len(result.warnings) > 0
        uc1.state.mark_done.assert_called_once()
        # State should be saved with "warning" status
        call_args = uc1.state.mark_done.call_args
        assert "warning" in call_args.args or "warning" in str(call_args)


class TestUC1Rollback:

    def test_rollback_triggered_on_failure(self):
        client = make_mock_client(
            feature_templates=make_feature_templates([
                ("cisco-tracker-template", "cisco_tracker", "tracker-tid-001"),
            ]),
            poll_result=poll_failure(),
        )
        rollback = MagicMock(spec=RollbackService)
        rollback.rollback.return_value = "success"
        state = MagicMock(spec=StateService)
        state.is_done.return_value = (False, {})
        backup = MagicMock(spec=BackupService)
        backup.save.return_value = "/tmp/backup.json"
        diff   = MagicMock(spec=DiffService)
        diff.generate.return_value = {"diff_summary": ""}

        uc1 = UC1TrackerEnable(client, state, backup, rollback, DiffService.__new__(DiffService), ValidationService())
        uc1.diff = diff
        site = make_site()

        result = uc1.run(site, dry_run=False, force=False)

        assert result.status == UCStatus.FAILED
        rollback.rollback.assert_called_once()
        uc1.state.mark_done.assert_not_called()

    def test_rollback_on_timeout(self):
        client = make_mock_client(
            feature_templates=make_feature_templates([
                ("cisco-tracker-template", "cisco_tracker", "tracker-tid-001"),
            ]),
            poll_result=poll_timeout(),
        )
        rollback = MagicMock(spec=RollbackService)
        rollback.rollback.return_value = "success"
        state = MagicMock(spec=StateService)
        state.is_done.return_value = (False, {})
        backup = MagicMock(spec=BackupService)
        backup.save.return_value = "/tmp/backup.json"
        diff = MagicMock(spec=DiffService)
        diff.generate.return_value = {"diff_summary": ""}

        uc1  = UC1TrackerEnable(client, state, backup, rollback, diff, ValidationService())
        site = make_site()

        result = uc1.run(site, dry_run=False, force=False)

        assert result.status == UCStatus.FAILED
        rollback.rollback.assert_called_once()
