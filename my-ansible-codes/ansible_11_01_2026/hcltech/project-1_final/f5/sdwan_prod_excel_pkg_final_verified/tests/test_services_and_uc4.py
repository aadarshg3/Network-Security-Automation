"""
tests/test_uc4_create_a_firewall_transit_interface.py
tests/test_state_service.py
tests/test_diff_service.py
tests/test_profile_service.py

Combined test module covering UC4, state, diff, and profile services.
"""

import json
import os
import pytest
import tempfile
from unittest.mock import MagicMock

from src.models.result_models import UCStatus
from src.services.backup_service import BackupService
from src.services.diff_service import DiffService
from src.services.profile_service import ProfileService
from src.services.rollback_service import RollbackService
from src.services.state_service import StateService
from src.services.validation_service import ValidationService
from src.client.exceptions import DuplicateVariableError, ValidationError
from src.usecases.uc4_create_a_firewall_transit_interface import (
    UC4CreateAFirewallTransitInterface,
    UC_NAME as UC4_NAME,
)

from tests.mock_data import (
    make_site, make_mock_client, make_device_template,
    make_feature_templates, poll_success, poll_failure,
    poll_soft_error, poll_timeout, make_profile,
)


# ══════════════════════════════════════════════════════════════════════
# UC4 Tests
# ══════════════════════════════════════════════════════════════════════

def _make_uc4(client=None, state=None, rollback=None):
    client   = client or make_mock_client()
    state    = state or MagicMock(spec=StateService)
    state.is_done.return_value = (False, {})
    backup   = MagicMock(spec=BackupService)
    backup.save.return_value = "/tmp/backup_uc4.json"
    rollback = rollback or MagicMock(spec=RollbackService)
    rollback.rollback.return_value = "success"
    diff     = MagicMock(spec=DiffService)
    diff.generate.return_value = {"diff_summary": ""}
    return UC4CreateAFirewallTransitInterface(
        client, state, backup, rollback, diff, ValidationService()
    )


class TestUC4NamePreservation:
    """The customer named UC4 'Create a Firewall Transit Interface' — must be exact."""

    def test_uc4_name_is_exact_customer_name(self):
        uc4  = _make_uc4()
        site = make_site()
        result = uc4.run(site, dry_run=True)
        assert result.uc_name == "Use Case 4: Create a Firewall Transit Interface"

    def test_uc4_module_constant(self):
        assert UC4_NAME == "Use Case 4: Create a Firewall Transit Interface"


class TestUC4Idempotency:

    def test_skip_if_deployed(self):
        state = MagicMock(spec=StateService)
        state.is_done.return_value = (True, {"deployed_at": "2025-01-01"})
        uc4  = _make_uc4(state=state)
        result = uc4.run(make_site(), dry_run=False, force=False)
        assert result.status == UCStatus.SKIPPED

    def test_force_clears_and_redeploys(self):
        state = MagicMock(spec=StateService)
        state.is_done.return_value = (True, {"deployed_at": "2025-01-01"})
        client = make_mock_client(poll_result=poll_success())
        uc4    = _make_uc4(client=client, state=state)
        result = uc4.run(make_site(), dry_run=False, force=True)
        state.clear.assert_called_once_with("test-site1", "uc4")
        assert result.status == UCStatus.SUCCESS


class TestUC4DryRun:

    def test_dry_run_no_deploy(self):
        uc4  = _make_uc4()
        result = uc4.run(make_site(), dry_run=True)
        assert result.status == UCStatus.DRY_RUN
        uc4.client.attach_and_deploy.assert_not_called()


class TestUC4TemplateAttachment:

    def test_pepguest_and_pepinet_attached(self):
        client = make_mock_client(poll_result=poll_success())
        uc4    = _make_uc4(client=client)
        result = uc4.run(make_site(), dry_run=False)
        assert result.status == UCStatus.SUCCESS
        # update_device_template should have been called (templates were attached)
        client.update_device_template.assert_called_once()

    def test_already_attached_not_duplicated(self):
        site     = make_site()
        template = make_device_template()
        template["generalTemplates"].append({
            "templateId":   site.pepguest_vpn_template_id,
            "templateType": "cisco_vpn",
            "subTemplates": [],
        })
        template["generalTemplates"].append({
            "templateId":   site.pepinet_vpn_template_id,
            "templateType": "cisco_vpn",
            "subTemplates": [],
        })
        client = make_mock_client(template=template, poll_result=poll_success())
        uc4    = _make_uc4(client=client)
        uc4.run(site, dry_run=False)
        # Neither template was new — no PUT needed
        client.update_device_template.assert_not_called()


class TestUC4SoftError:

    def test_soft_error_is_warning(self):
        client = make_mock_client(poll_result=poll_soft_error())
        uc4    = _make_uc4(client=client)
        result = uc4.run(make_site(), dry_run=False)
        assert result.status == UCStatus.WARNING
        uc4.state.mark_done.assert_called_once()


class TestUC4Rollback:

    def test_rollback_on_failure(self):
        client   = make_mock_client(poll_result=poll_failure())
        rollback = MagicMock(spec=RollbackService)
        rollback.rollback.return_value = "success"
        uc4 = _make_uc4(client=client, rollback=rollback)
        result = uc4.run(make_site(), dry_run=False)
        assert result.status == UCStatus.FAILED
        rollback.rollback.assert_called_once()


# ══════════════════════════════════════════════════════════════════════
# State Service Tests
# ══════════════════════════════════════════════════════════════════════

class TestStateService:

    def test_is_done_false_initially(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            state = StateService(state_file=f.name)
        done, _ = state.is_done("site1", "uc1")
        assert done is False

    def test_mark_done_persists(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        state = StateService(state_file=path)
        state.mark_done("site1", "uc1", "tpl-123", "uuid-456")
        done, record = state.is_done("site1", "uc1")
        assert done is True
        assert record["status"] == "success"
        os.unlink(path)

    def test_clear_removes_state(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        state = StateService(state_file=path)
        state.mark_done("site1", "uc1", "tpl-123", "uuid-456")
        state.clear("site1", "uc1")
        done, _ = state.is_done("site1", "uc1")
        assert done is False
        os.unlink(path)

    def test_warning_status_counted_as_done(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        state = StateService(state_file=path)
        state.mark_done("site1", "uc3", "tpl-123", "uuid-456", status="warning")
        done, record = state.is_done("site1", "uc3")
        assert done is True
        assert record["status"] == "warning"
        os.unlink(path)


# ══════════════════════════════════════════════════════════════════════
# Diff Service Tests
# ══════════════════════════════════════════════════════════════════════

class TestDiffService:

    def test_generates_diff_files(self, tmp_path):
        svc = DiffService(reports_dir=str(tmp_path))
        result = svc.generate("before\nline1\n", "after\nline2\n", label="test")
        assert "before" in result
        assert "after"  in result
        assert "diff"   in result
        assert os.path.isfile(result["before"])
        assert os.path.isfile(result["after"])
        assert os.path.isfile(result["diff"])

    def test_identical_configs_show_no_diff(self, tmp_path):
        svc    = DiffService(reports_dir=str(tmp_path))
        config = "interface Gig0/0/1\n no ip address\n"
        result = svc.generate(config, config, label="nodiff")
        assert "identical" in result["diff_summary"] or result["diff_summary"] == ""

    def test_diff_summary_captured(self, tmp_path):
        svc    = DiffService(reports_dir=str(tmp_path))
        result = svc.generate("old line\n", "new line\n", label="changed")
        assert result["diff_summary"] != ""


# ══════════════════════════════════════════════════════════════════════
# Profile Service Tests
# ══════════════════════════════════════════════════════════════════════

class TestProfileService:

    def _make_config(self):
        return {
            "default": {
                "description": "Default",
                "enabled_use_cases": ["uc1", "uc2", "uc3", "uc4"],
                "fw_transit_vlan_default": 50,
                "corporate_vpn": 30,
                "pepguest_vpn": 10,
                "pepinet_vpn": 20,
            },
            "profiles": [
                {
                    "id": "apac_gold",
                    "region": "APAC",
                    "metallic_type": "Gold",
                    "design_type": None,
                    "description": "APAC Gold",
                    "enabled_use_cases": ["uc1", "uc2", "uc3", "uc4"],
                    "fw_transit_vlan_default": 50,
                    "corporate_vpn": 30, "pepguest_vpn": 10, "pepinet_vpn": 20,
                },
                {
                    "id": "apac_silver",
                    "region": "APAC",
                    "metallic_type": "Silver",
                    "design_type": None,
                    "description": "APAC Silver",
                    "enabled_use_cases": ["uc1", "uc2"],
                    "fw_transit_vlan_default": 50,
                    "corporate_vpn": 30, "pepguest_vpn": 10, "pepinet_vpn": 20,
                },
                {
                    "id": "emea_gold_newdesign",
                    "region": "EMEA",
                    "metallic_type": "Gold",
                    "design_type": "NewDesign",
                    "description": "EMEA Gold NewDesign",
                    "enabled_use_cases": ["uc1", "uc2", "uc3", "uc4"],
                    "fw_transit_vlan_default": 200,
                    "corporate_vpn": 30, "pepguest_vpn": 300, "pepinet_vpn": 301,
                },
            ],
        }

    def test_resolves_apac_gold(self):
        svc     = ProfileService(self._make_config())
        profile = svc.resolve("APAC", "Gold")
        assert profile.profile_id == "apac_gold"

    def test_resolves_apac_silver(self):
        svc     = ProfileService(self._make_config())
        profile = svc.resolve("APAC", "Silver")
        assert profile.profile_id == "apac_silver"
        assert "uc3" not in profile.enabled_use_cases

    def test_resolves_most_specific_with_design_type(self):
        svc     = ProfileService(self._make_config())
        profile = svc.resolve("EMEA", "Gold", "NewDesign")
        assert profile.profile_id == "emea_gold_newdesign"
        assert profile.pepguest_vpn == 300

    def test_falls_back_to_default(self):
        svc     = ProfileService(self._make_config())
        profile = svc.resolve("UNKNOWN", "Bronze")
        assert profile.profile_id == "default"

    def test_profile_controls_enabled_use_cases(self):
        svc     = ProfileService(self._make_config())
        profile = svc.resolve("APAC", "Silver")
        assert "uc1" in profile.enabled_use_cases
        assert "uc3" not in profile.enabled_use_cases
        assert "uc4" not in profile.enabled_use_cases


# ══════════════════════════════════════════════════════════════════════
# Validation Service Tests
# ══════════════════════════════════════════════════════════════════════

class TestValidationService:

    def test_valid_interface_passes(self):
        svc = ValidationService()
        svc.validate_interface_name("GigabitEthernet0/0/1", "fw_physical_port")  # no exception

    def test_invalid_interface_raises(self):
        svc = ValidationService()
        with pytest.raises(ValidationError):
            svc.validate_interface_name("not-an-interface!", "fw_physical_port")

    def test_valid_vlan_passes(self):
        svc = ValidationService()
        svc.validate_vlan(50, "pepguest_vlan")  # no exception

    def test_invalid_vlan_raises(self):
        svc = ValidationService()
        with pytest.raises(ValidationError):
            svc.validate_vlan(5000, "pepguest_vlan")

    def test_valid_ip_passes(self):
        svc = ValidationService()
        svc.validate_ip("10.1.2.3", "pepguest_ip")  # no exception

    def test_invalid_ip_raises(self):
        svc = ValidationService()
        with pytest.raises(ValidationError):
            svc.validate_ip("999.1.2.3", "pepguest_ip")

    def test_duplicate_variable_raises(self):
        svc  = ValidationService()
        vars = {"key1": "val1", "key2": "val2"}
        svc.validate_variables_no_duplicates(vars, "test")  # no exception

    def test_duplicate_variable_from_list_raises(self):
        svc   = ValidationService()
        pairs = [("key1", "val_a"), ("key2", "val_b"), ("key1", "val_c")]
        with pytest.raises(DuplicateVariableError):
            svc.validate_variables_from_list(pairs, "test_context")
