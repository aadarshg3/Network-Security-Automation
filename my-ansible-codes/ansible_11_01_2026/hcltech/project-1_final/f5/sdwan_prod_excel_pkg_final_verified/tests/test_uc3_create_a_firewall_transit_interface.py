from unittest.mock import MagicMock

from src.models.result_models import UCStatus
from src.services.backup_service import BackupService
from src.services.diff_service import DiffService
from src.services.rollback_service import RollbackService
from src.services.state_service import StateService
from src.services.validation_service import ValidationService
from src.usecases.uc3_create_a_firewall_transit_interface import UC3CreateAFirewallTransitInterface

from tests.mock_data import make_device_template, make_mock_client, make_site, poll_success


def _make_uc3(client=None, state=None, rollback=None):
    client = client or make_mock_client()
    state = state or MagicMock(spec=StateService)
    state.is_done.return_value = (False, {})
    backup = MagicMock(spec=BackupService)
    backup.save.return_value = "/tmp/backup_uc3.json"
    rollback = rollback or MagicMock(spec=RollbackService)
    rollback.rollback.return_value = "success"
    diff = MagicMock(spec=DiffService)
    diff.generate.return_value = {"diff_summary": ""}
    return UC3CreateAFirewallTransitInterface(client, state, backup, rollback, diff, ValidationService())


def test_uc3_attaches_noip_template_to_real_vpn0_block():
    template = make_device_template()
    client = make_mock_client(template=template, poll_result=poll_success())
    uc3 = _make_uc3(client=client)

    result = uc3.run(make_site(), dry_run=False)

    assert result.status == UCStatus.SUCCESS
    payload = client.update_device_template.call_args.args[1]
    vpn0_block = payload["generalTemplates"][0]
    assert any(item["templateId"] == "noip-tid-001" for item in vpn0_block["subTemplates"])


def test_uc3_applies_logical_subinterface_name():
    uc3 = _make_uc3()
    row = uc3._apply_variables({}, make_site({"fw_physical_port": "GigabitEthernet0/0/0", "fw_transit_vlan": 50}))

    assert row["/3/INT03_NO-DHCP-HELPER_interface_NAME/interface/if-name"] == "GigabitEthernet0/0/0.50"


def test_uc3_dry_run_does_not_deploy():
    uc3 = _make_uc3()
    result = uc3.run(make_site(), dry_run=True)

    assert result.status == UCStatus.DRY_RUN
    uc3.client.attach_and_deploy.assert_not_called()
