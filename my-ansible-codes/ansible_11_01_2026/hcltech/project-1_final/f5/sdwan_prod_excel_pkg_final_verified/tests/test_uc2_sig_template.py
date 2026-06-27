from unittest.mock import MagicMock

from src.models.result_models import UCStatus
from src.services.backup_service import BackupService
from src.services.diff_service import DiffService
from src.services.rollback_service import RollbackService
from src.services.state_service import StateService
from src.services.validation_service import ValidationService
from src.usecases.uc2_sig_template import UC2SIGTemplate

from tests.mock_data import make_mock_client, make_site, poll_success


def _make_uc2(client=None, state=None, rollback=None):
    client = client or make_mock_client()
    state = state or MagicMock(spec=StateService)
    state.is_done.return_value = (False, {})
    backup = MagicMock(spec=BackupService)
    backup.save.return_value = "/tmp/backup_uc2.json"
    rollback = rollback or MagicMock(spec=RollbackService)
    rollback.rollback.return_value = "success"
    diff = MagicMock(spec=DiffService)
    diff.generate.return_value = {"diff_summary": ""}
    return UC2SIGTemplate(client, state, backup, rollback, diff, ValidationService())


def test_uc2_attaches_sig_under_vpn0_and_credentials_top_level():
    client = make_mock_client(poll_result=poll_success())
    uc2 = _make_uc2(client=client)
    result = uc2.run(make_site(), dry_run=False)

    assert result.status == UCStatus.SUCCESS
    payload = client.update_device_template.call_args.args[1]
    vpn0_block = payload["generalTemplates"][0]
    assert any(item["templateId"] == "sig-tid-001" for item in vpn0_block["subTemplates"])
    assert any(item["templateId"] == "sig-cred-tid-001" for item in payload["generalTemplates"])


def test_uc2_dry_run_does_not_deploy():
    uc2 = _make_uc2()
    result = uc2.run(make_site(), dry_run=True)

    assert result.status == UCStatus.DRY_RUN
    uc2.client.attach_and_deploy.assert_not_called()
