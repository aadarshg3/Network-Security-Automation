import argparse
import getpass
import logging
import os
import sys
from datetime import datetime

os.makedirs("logs", exist_ok=True)
_logfile = os.path.join("logs", f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_sdwan.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s - %(message)s",
    handlers=[logging.FileHandler(_logfile), logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("sdwan.main")

from src.excel_loader import load as load_excel
from src.vmanage_client import VManageClient
from src.backup import save as save_backup, load as load_backup
from src.diff_report import show_and_save as show_diff
from src import state
import src.uc1_tracker     as uc1
import src.uc2_sig         as uc2
import src.uc3_service_vpn as uc3

UC_MAP = {1: uc1, 2: uc2, 3: uc3}


def main():
    parser = argparse.ArgumentParser(description="SD-WAN Zscaler Automation UC1/UC2/UC3")
    parser.add_argument("--uc",      nargs="+", type=int, choices=[1, 2, 3], required=True)
    parser.add_argument("--excel",   default="configs/newvalues.xlsx")
    parser.add_argument("--dry-run", action="store_true", help="Preview diff only, no deploy")
    parser.add_argument("--force",   action="store_true", help="Run even if already deployed")
    parser.add_argument("--status",  action="store_true", help="Show deployment state and exit")
    args = parser.parse_args()

    if args.status:
        print("\nDeployment State")
        print("-" * 40)
        state.show_all()
        sys.exit(0)

    try:
        cfg = load_excel(args.excel)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR loading Excel: {e}")
        sys.exit(1)

    print()
    print("SD-WAN Zscaler Automation")
    print("=" * 50)
    print(f"Use Cases : {args.uc}")
    print(f"vManage   : {cfg['vmanage']['host']}")
    print(f"Mode      : {'DRY-RUN' if args.dry_run else 'LIVE DEPLOY'}")
    print(f"Force     : {args.force}")
    print(f"Log       : {_logfile}")
    print("=" * 50)
    print()

    # ── Confirm BEFORE login/API calls to avoid MTEMP0015 session expiry ──
    if not args.dry_run:
        uc_list = sorted(set(args.uc))
        print(f"This will LIVE deploy UC{uc_list} to the device.")
        print("Run with --dry-run first to preview changes.")
        choice = input("Proceed? [Y/N]: ").strip().lower()
        if choice != "y":
            print("Aborted.")
            sys.exit(0)
        print()

    password = os.environ.get("VMANAGE_PASSWORD") or \
               getpass.getpass(f"Password for '{cfg['vmanage']['username']}': ")

    client = VManageClient(cfg["vmanage"]["host"])
    try:
        client.login(cfg["vmanage"]["username"], password)
    except Exception as e:
        print(f"ERROR: Login failed: {e}")
        sys.exit(1)
    print("Login OK\n")

    for uc_num in sorted(set(args.uc)):
        _run_uc(client, cfg, UC_MAP[uc_num], uc_num, args)


def _run_uc(client, cfg, module, uc_num, args):
    uc_key      = f"uc{uc_num}"
    template_id = cfg[uc_key]["device_template_id"]
    device_uuid = cfg[uc_key]["device_uuid"]
    backup_path = None

    print(f"\n{'=' * 50}")
    print(f"Running UC{uc_num}")
    print("=" * 50)

    print("Taking BEFORE config snapshot...")
    pre_config = _get_preview(client, template_id, device_uuid)
    if not pre_config:
        pre_config = "# Config not available - device not yet attached\n"
        print("  Not available - device not yet attached to template")
    else:
        print("  BEFORE snapshot captured")

    print("Saving template backup...")
    try:
        backup_path = save_backup(f"uc{uc_num}_before", template_id, client.get_device_template(template_id))
        print(f"  Backup: {backup_path}")
    except Exception as e:
        print(f"  WARNING: Backup failed: {e}")
        logger.warning(f"Backup failed UC{uc_num}: {e}")

    try:
        inputs, template_id, template_changed = module.run(client, cfg, force=args.force)
    except Exception as e:
        print(f"ERROR in UC{uc_num}: {e}")
        logger.error(f"UC{uc_num} failed: {e}")
        _rollback(client, template_id, backup_path, f"UC{uc_num} error: {e}")
        return

    if inputs is None:
        return

    print("\nTaking AFTER config preview...")
    post_config = _get_preview(client, template_id, inputs[0])
    if not post_config or "error" in post_config[:40].lower():
        post_config = "# Post-config preview not available\n"
        print("  Not available")
    else:
        print("  AFTER preview captured")

    diff_paths = show_diff(pre_config, post_config)
    print(f"\n  BEFORE : {diff_paths.get('pre',  'N/A')}")
    print(f"  AFTER  : {diff_paths.get('post', 'N/A')}")
    print(f"  Diff   : {diff_paths.get('diff', 'N/A')}")
    print(f"  Excel  : {diff_paths.get('excel','N/A')}")

    print(f"\nVariables applied (UC{uc_num}):")
    for k, v in inputs[0].items():
        if not k.startswith("csv"):
            print(f"  {k} = {v}")

    if args.dry_run:
        print(f"\nDRY-RUN complete - no changes deployed")
        return

    # Deploy immediately - no pause - session is always fresh here
    print(f"\nDeploying UC{uc_num}...")
    try:
        action_id = client.attach_and_deploy(template_id, inputs, is_edited=template_changed)
    except Exception as e:
        print(f"ERROR: Deploy call failed: {e}")
        logger.error(f"Deploy failed UC{uc_num}: {e}")
        _rollback(client, template_id, backup_path, str(e))
        return

    print(f"Deploy triggered - action_id: {action_id}")
    print("Polling status (up to 180s)...")
    result = client.poll_task(action_id, timeout=180)

    if result["status"] == "timeout":
        print(f"\nTIMEOUT - no response within 180s")
        print(f"Action ID: {action_id}")
        print("Check vManage Monitor -> Tasks manually")
        logger.error(f"Deploy timeout UC{uc_num} action_id={action_id}")
        _rollback(client, template_id, backup_path, "deploy timeout")

    elif result["failure"] > 0:
        print(f"\nDEPLOY FAILED on {result['failure']} device(s)")
        for item in result.get("data", []):
            print(f"  Device : {item.get('host-name', 'unknown')}")
            print(f"  Reason : {item.get('currentActivity', '')[:200]}")
        logger.error(f"Deploy failure UC{uc_num}: {result}")
        _rollback(client, template_id, backup_path, "device reported failure")

    else:
        print(f"\nUC{uc_num} DEPLOYED SUCCESSFULLY")
        print(f"  {result['success']} device(s) updated")
        print("  Verify: vManage -> Monitor -> Network -> device -> Config")
        logger.info(f"UC{uc_num} deploy success action_id={action_id}")
        state.mark_done(uc_key, template_id, device_uuid)
        print(f"  State saved to sdwan_state.json - UC{uc_num} will not run again")
        print(f"  Backup: {backup_path}")


def _rollback(client, template_id, backup_path, reason):
    print()
    print("AUTOMATIC ROLLBACK TRIGGERED")
    print(f"  Reason: {reason}")
    logger.warning(f"Rollback triggered: {reason}")

    if not backup_path:
        print("  ERROR: No backup available - restore manually from vManage UI")
        logger.error("Rollback failed - no backup path")
        return

    print(f"  Loading backup: {backup_path}")
    try:
        backup_data = load_backup(backup_path)
    except FileNotFoundError as e:
        print(f"  ERROR: Backup file missing: {e}")
        logger.error(f"Rollback failed - missing backup: {e}")
        return

    print("  Restoring template to pre-change state...")
    try:
        client.rollback_device_template(template_id, backup_data)
        print("  ROLLBACK SUCCESSFUL")
        print(f"  Backup used: {backup_path}")
        logger.info(f"Rollback successful template={template_id[:8]}...")
    except Exception as e:
        print(f"  ROLLBACK FAILED: {e}")
        print(f"  Manual restore required. Backup: {backup_path}")
        logger.error(f"Rollback PUT failed: {e}")


def _get_preview(client, template_id, device_ref):
    try:
        if isinstance(device_ref, str):
            inputs = client.get_inputs(template_id, device_ref)
            if not inputs:
                return ""
            row = dict(inputs[0])
        else:
            row = dict(device_ref)
        preview = client.get_config_preview(template_id, row)
        if preview and "error" not in preview[:40].lower():
            return preview
    except Exception as e:
        logger.warning(f"Config preview failed: {e}")
    return ""


if __name__ == "__main__":
    main()
