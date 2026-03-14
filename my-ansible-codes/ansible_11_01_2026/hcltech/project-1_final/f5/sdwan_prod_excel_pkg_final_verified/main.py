#!/usr/bin/env python3
"""
Excel-driven SD-WAN automation CLI for customer Use Cases 1-4.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from copy import deepcopy

from src.client.vmanage_client import VManageClient
from src.orchestrator.cutover_runner import CutoverRunner, UC_ORDER
from src.services.excel_config_loader import DEFAULT_EXCEL_PATH, load_excel_config
from src.services.state_service import StateService
from src.utils.logger import setup_logging

VALID_UCS = ["uc1", "uc2", "uc3", "uc4"]


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    bundle = load_excel_config(args.excel)
    settings = deepcopy(bundle.settings)
    _apply_connection_overrides(settings, args)
    paths = bundle.settings.get("paths", {})
    log_cfg = settings.get("logging", {})
    log_file = setup_logging(
        level=log_cfg.get("level", "INFO"),
        logs_dir=paths.get("logs_dir", "logs"),
        fmt=log_cfg.get("format", "%(asctime)s  %(levelname)-8s  %(name)s - %(message)s"),
    )

    import logging

    logger = logging.getLogger("sdwan.main")
    logger.info("SD-WAN automation starting - log: %s", log_file)

    site_name = args.site or bundle.site.site_name
    if args.status:
        state = StateService(state_file=paths.get("state_file", "sdwan_state.json"))
        print("\nDeployment State")
        print("-" * 50)
        site_state = state.get_site_state(site_name)
        if not site_state:
            print(f"  No deployments recorded for site: {site_name}")
        else:
            for uc, rec in site_state.items():
                print(f"  {uc}: {rec.get('status')} at {rec.get('deployed_at')}")
        return 0

    if args.discover_lab:
        username = settings["vmanage"].get("username", "admin")
        password = os.environ.get("VMANAGE_PASSWORD") or getpass.getpass(
            f"Password for '{username}' at {settings['vmanage'].get('host', '')}: "
        )
        return _discover_lab(settings, password)

    uc_keys = _resolve_uc_keys(parser, args)

    print()
    print("SD-WAN Site Cutover Automation")
    print("=" * 60)
    print(f"  Excel     : {bundle.excel_path}")
    print(f"  Site      : {site_name}")
    print(f"  Use Cases : {uc_keys}")
    print(f"  vManage   : {settings['vmanage'].get('host', '')}")
    print(f"  Mode      : {'DRY-RUN' if args.dry_run else 'LIVE DEPLOY'}")
    print(f"  Report dir: {args.report_dir}")
    if bundle.warnings:
        print(f"  Warnings  : {', '.join(bundle.warnings)}")
    print("=" * 60)
    print()

    host = settings["vmanage"].get("host", "")
    if not host:
        print("ERROR: vManage host is empty in the Excel workbook.")
        return 1
    if _looks_like_placeholder_host(host):
        print("ERROR: vManage host is still a placeholder value.")
        print("Set it in configs/sdwan_config.xlsx or pass --vmanage-host https://172.17.152.161")
        return 1

    if not args.dry_run:
        print(f"This will LIVE deploy {uc_keys} for site '{site_name}'.")
        print("Use --dry-run first to preview all changes safely.")
        if input("Proceed? [Y/N]: ").strip().lower() != "y":
            print("Aborted.")
            return 0
        print()

    username = settings["vmanage"].get("username", "admin")
    password = os.environ.get("VMANAGE_PASSWORD") or getpass.getpass(
        f"Password for '{username}' at {settings['vmanage'].get('host', '')}: "
    )

    runner = CutoverRunner(settings=settings, profiles_config={"default": {}})
    try:
        report = runner.run(
            site_name=site_name,
            uc_keys=uc_keys,
            password=password,
            dry_run=args.dry_run,
            force=args.force,
            report_dir=args.report_dir,
            site_override=bundle.site,
            profile_override=bundle.profile,
        )
    except Exception as exc:
        logger.error("Cutover failed with unhandled error: %s", exc, exc_info=True)
        return 1

    print()
    print("=" * 60)
    print(f"  Run complete - Overall status: {report.overall_status}")
    print(f"  Success : {report.success_count}")
    print(f"  Skipped : {report.skipped_count}")
    print(f"  Failed  : {report.failed_count}")
    print("=" * 60)
    print()

    icons = {
        "success": "OK",
        "warning": "WARN",
        "failed": "FAIL",
        "skipped": "SKIP",
        "dry-run": "DRY",
        "rolled-back": "ROLLBACK",
    }
    for result in report.results:
        icon = icons.get(result.status.value, "?")
        print(f"  [{icon}] {result.uc_name:<50} [{result.display_status}]")
    print()

    return 0 if report.overall_status in ("SUCCESS", "WARNING", "SKIPPED", "DRY_RUN") else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="SD-WAN automation - Excel driven - UC1 / UC2 / UC3 / UC4"
    )
    parser.add_argument("--site", help="Optional override for the site name shown in reports")
    parser.add_argument("--uc", nargs="+", metavar="UC", help="Use case(s) to run: 1 2 3 4 or uc1 uc2 uc3 uc4")
    parser.add_argument("--run-all", action="store_true", help="Run all use cases")
    parser.add_argument("--dry-run", action="store_true", help="Preview only - no deployment")
    parser.add_argument("--force", action="store_true", help="Re-run even if already deployed")
    parser.add_argument("--status", action="store_true", help="Show deployment state and exit")
    parser.add_argument("--discover-lab", action="store_true", help="Print useful devices/templates from vManage")
    parser.add_argument("--report-dir", default="outputs", help="Directory for output reports")
    parser.add_argument("--excel", default=DEFAULT_EXCEL_PATH, help="Path to the customer Excel workbook")
    parser.add_argument("--vmanage-host", help="Override vManage host from Excel, e.g. https://172.17.152.161")
    parser.add_argument("--username", help="Override vManage username from Excel")
    return parser


def _resolve_uc_keys(parser: argparse.ArgumentParser, args) -> list[str]:
    if args.run_all:
        return list(UC_ORDER)
    if not args.uc:
        parser.error("Specify --uc <uc1 uc2 ...> or --run-all")
    uc_keys = [_normalise_uc(item) for item in args.uc]
    invalid = [item for item in uc_keys if item not in VALID_UCS]
    if invalid:
        parser.error(f"Invalid UC key(s): {invalid}. Valid options: {VALID_UCS}")
    return uc_keys


def _normalise_uc(value: str) -> str:
    value = value.strip().lower()
    if value in {"1", "2", "3", "4"}:
        return f"uc{value}"
    return value


def _apply_connection_overrides(settings: dict, args) -> None:
    vm_cfg = settings.setdefault("vmanage", {})
    host_override = args.vmanage_host or os.environ.get("VMANAGE_HOST")
    user_override = args.username or os.environ.get("VMANAGE_USERNAME")
    if host_override:
        vm_cfg["host"] = host_override.strip()
    if user_override:
        vm_cfg["username"] = user_override.strip()


def _looks_like_placeholder_host(host: str) -> bool:
    normalised = host.strip().lower()
    return normalised in {
        "",
        "https://vmanage-ip",
        "http://vmanage-ip",
        "vmanage-ip",
        "https://",
        "http://",
    }


def _discover_lab(settings: dict, password: str) -> int:
    host = settings["vmanage"].get("host", "")
    username = settings["vmanage"].get("username", "admin")
    if not host or _looks_like_placeholder_host(host):
        print("ERROR: set a real vManage host before using --discover-lab")
        return 1

    client = VManageClient(
        host=host,
        verify_ssl=settings["vmanage"].get("verify_ssl", False),
        timeout=settings["vmanage"].get("timeout_seconds", 30),
        retry_attempts=settings["vmanage"].get("retry_attempts", 3),
        retry_delay=settings["vmanage"].get("retry_delay_seconds", 5.0),
        poll_timeout=settings["vmanage"].get("poll_timeout_seconds", 180),
        poll_interval=settings["vmanage"].get("poll_interval_seconds", 5),
    )
    try:
        client.login(username, password)
        devices = client.list_devices()
        device_templates = client.list_device_templates()
        feature_templates = client.list_feature_templates()
    finally:
        try:
            client.logout()
        except Exception:
            pass

    print("\nDevices")
    print("-" * 70)
    for item in devices:
        name = item.get("host-name", "")
        if item.get("personality") == "vedge" or "cedge" in name.lower():
            print(
                f"{name:20} system-ip={item.get('system-ip','')} "
                f"uuid={item.get('uuid','')} model={item.get('device-model','')}"
            )

    print("\nDevice Templates")
    print("-" * 70)
    for item in device_templates:
        name = item.get("templateName", "")
        if any(key in name.lower() for key in ("uc", "lab", "c8000v")):
            print(f"{name:35} id={item.get('templateId','')}")

    print("\nFeature Templates")
    print("-" * 70)
    keywords = ("uc", "sig", "zscaler", "tracker", "nat", "pep", "guest", "inet", "firewall", "transit", "corp")
    for item in feature_templates:
        name = item.get("templateName", "")
        desc = item.get("templateDescription", "")
        blob = f"{name} {desc}".lower()
        if any(key in blob for key in keywords):
            print(f"{item.get('templateType',''):32} {name:35} id={item.get('templateId','')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
