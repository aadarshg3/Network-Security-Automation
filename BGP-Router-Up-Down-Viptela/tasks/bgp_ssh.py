#!/usr/bin/env python3
"""SSH execution script for BGP-Router-Up-Down-Viptela playbook.

Supports exec commands (show + clear), and config-mode operations
per platform (cedge: config-transaction/commit, vedge: config/commit).
Returns JSON: {"failed": bool, "msg": str, "output": dict}.
"""
import sys
import json
import time
from hashlib import md5

try:
    from netmiko import ConnectHandler, NetmikoTimeoutException
    import paramiko
except ImportError as e:
    print(json.dumps({"failed": True, "msg": f"Import error: {e}"}))
    sys.exit(1)

_md5_bypass_done = False


def _bypass_md5() -> None:
    """Patch md5 to bypass FIPS usedforsecurity restriction."""
    global _md5_bypass_done
    if _md5_bypass_done:
        return
    orig_init = md5.__init__

    def _new_init(self, *args, **kwargs):
        kwargs["usedforsecurity"] = False
        orig_init(self, *args, **kwargs)

    md5.__init__ = _new_init
    _md5_bypass_done = True


def _connect(device: dict) -> tuple:
    """Establish SSH connection with md5-bypass retry on FIPS systems.

    Args:
        device: Netmiko connection dict.

    Returns:
        tuple: (ConnectHandler | None, bool, str)
    """
    try:
        return ConnectHandler(**device), True, "OK"
    except paramiko.AuthenticationException as exc:
        return None, False, f"Auth failed: {exc}"
    except ValueError as exc:
        _bypass_md5()
        try:
            return ConnectHandler(**device), True, "OK"
        except Exception as exc2:
            return None, False, f"ValueError after bypass: {exc2}"
    except Exception as exc:
        return None, False, str(exc)


def _run_exec_commands(conn, commands: list) -> dict:
    """Send exec-mode commands and collect output.

    Args:
        conn: Active Netmiko connection.
        commands: List of commands to send.

    Returns:
        dict: command -> output mapping.
    """
    output = {}
    for cmd in commands:
        try:
            output[cmd] = conn.send_command(cmd, read_timeout=60)
        except Exception as exc:
            output[cmd] = f"ERROR: {exc}"
    return output


def _bounce_cedge(conn, config_cmds: list, post_cmds: list) -> str:
    """Execute cEdge interface bounce via config-transaction/commit.

    Args:
        conn: Active Netmiko connection.
        config_cmds: Commands for first config block (shutdown).
        post_cmds: Commands for second config block (no shutdown).

    Returns:
        str: Combined output from both config blocks.
    """
    out = []
    try:
        conn.send_command("config-transaction", expect_string=r"#", read_timeout=15)
        for cmd in config_cmds:
            out.append(conn.send_command(cmd, expect_string=r"#", read_timeout=15))
        out.append(conn.send_command("commit", expect_string=r"#", read_timeout=30))
        time.sleep(3)
        conn.send_command("config-transaction", expect_string=r"#", read_timeout=15)
        for cmd in post_cmds:
            out.append(conn.send_command(cmd, expect_string=r"#", read_timeout=15))
        out.append(conn.send_command("commit", expect_string=r"#", read_timeout=30))
    except Exception as exc:
        out.append(f"ERROR during config: {exc}")
    return "\n".join(out)


def _bounce_vedge(conn, config_cmds: list, post_cmds: list) -> str:
    """Execute vEdge interface bounce via config/commit.

    Args:
        conn: Active Netmiko connection.
        config_cmds: Commands for shutdown block (vpn + interface + shutdown).
        post_cmds: Commands for no-shutdown block.

    Returns:
        str: Combined output.
    """
    out = []
    try:
        conn.send_command("config", expect_string=r"#", read_timeout=15)
        for cmd in config_cmds:
            out.append(conn.send_command(cmd, expect_string=r"#", read_timeout=15))
        out.append(conn.send_command("commit", expect_string=r"#", read_timeout=30))
        time.sleep(3)
        for cmd in post_cmds:
            out.append(conn.send_command(cmd, expect_string=r"#", read_timeout=15))
        out.append(conn.send_command("commit", expect_string=r"#", read_timeout=30))
        conn.send_command("exit", expect_string=r"#", read_timeout=10)
    except Exception as exc:
        out.append(f"ERROR during config: {exc}")
    return "\n".join(out)


def main() -> None:
    """Parse args, connect, run commands, return JSON result."""
    if len(sys.argv) < 2:
        print(json.dumps({"failed": True, "msg": "No arguments provided"}))
        sys.exit(1)

    try:
        args = json.loads(sys.argv[1])
    except Exception as exc:
        print(json.dumps({"failed": True, "msg": f"Args parse error: {exc}"}))
        sys.exit(1)

    host = args.get("host", "")
    username = args.get("username", "")
    password = args.get("password", "")
    enable_password = args.get("enable_password", "")
    device_type = args.get("device_type", "cisco_ios")
    commands = args.get("commands", [])
    config_mode = args.get("config_mode", "")
    config_commands = args.get("config_commands", [])
    post_config_commands = args.get("post_config_commands", [])
    verify_commands = args.get("verify_commands", [])

    device = {
        "device_type": device_type,
        "host": host,
        "username": username,
        "password": password,
        "timeout": 60,
        "global_delay_factor": 2,
    }
    if enable_password:
        device["secret"] = enable_password

    conn, ok, msg = _connect(device)
    if not ok:
        # sys.exit(1) is critical — Ansible.builtin.script sets .failed based
        # on exit code, NOT on JSON content. sys.exit(0) would make Ansible
        # see rc=0 (.failed=False) even though connection failed, causing
        # downstream tasks to incorrectly set ssh_ok=True.
        print(json.dumps({"failed": True, "msg": msg, "output": {}}))
        sys.exit(1)

    try:
        if enable_password:
            try:
                conn.enable()
            except Exception:
                pass

        output = {}

        if commands:
            output.update(_run_exec_commands(conn, commands))

        if config_mode == "cedge" and config_commands:
            output["config"] = _bounce_cedge(conn, config_commands, post_config_commands)

        if config_mode == "vedge" and config_commands:
            output["config"] = _bounce_vedge(conn, config_commands, post_config_commands)

        if verify_commands:
            output.update(_run_exec_commands(conn, verify_commands))

        conn.disconnect()
        print(json.dumps({"failed": False, "msg": "OK", "output": output}))

    except Exception as exc:
        try:
            conn.disconnect()
        except Exception:
            pass
        print(json.dumps({"failed": True, "msg": str(exc), "output": output if output else {}}))


if __name__ == "__main__":
    main()
