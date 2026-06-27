#!/usr/bin/env python3
"""
device_ssh.py — iAutomate SSH executor for Cisco-Router-Device-Down.

Usage:
  python3 device_ssh.py '<host>' '<user>' '<password>' '<commands_json>'
  python3 device_ssh.py '<host>' '<user>' '<password>' '<commands_json>' '<pre_check_json>'
  python3 device_ssh.py '<host>' '<user>' '<password>' '<commands_json>' '{}' '<config_cmds_json>'

Always exits 0. Errors are embedded in JSON stdout.
Ansible reads stdout and parses JSON — never sees a non-zero exit code.

JSON output structure:
  {
    "success": bool,
    "outputs": {"command": "output", ...},  # for multi-command runs
    "output": "...",                         # for single-command runs
    "error": null | "message",
    "privilege_denied": bool,
    "pre_check_failed": bool,
    "pre_check_output": "..."
  }
"""

import sys
import json
import logging
import re
import time

log = logging.getLogger('device_ssh')

# ---------------------------------------------------------------------------
# Netmiko import — graceful failure so Ansible gets JSON, not a traceback
# ---------------------------------------------------------------------------
try:
    from netmiko import ConnectHandler
    from netmiko.exceptions import (
        NetmikoAuthenticationException,
        NetmikoTimeoutException,
        NetMikoTimeoutException,
    )
    _NETMIKO_OK = True
except ImportError as _ie:
    _NETMIKO_OK = False
    _NETMIKO_IMPORT_ERROR = str(_ie)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CONN_TIMEOUT   = 30
AUTH_TIMEOUT   = 30
CMD_TIMEOUT    = 60
CONFIG_TIMEOUT = 30

_PRIV_DENIED_PATTERNS = re.compile(
    r'(privilege|denied|not authorized|authorization failed|'
    r'permission denied|access denied)',
    re.IGNORECASE
)

_ENABLE_FAILED_PATTERNS = re.compile(
    r'(invalid password|% access denied|% error|bad secrets)',
    re.IGNORECASE
)


# ---------------------------------------------------------------------------
# Core SSH executor
# ---------------------------------------------------------------------------

def _run(host, username, password, commands, pre_check=None, config_commands=None,
         platform='ios'):
    """
    Execute commands via SSH.

    commands       : list of show commands (each gets its own output entry)
    pre_check      : {'command': str, 'must_contain': str} — safety gate
    config_commands: list of config-mode commands (run only if pre_check passes)
    platform       : ios | ios_xe | ios_xr (selects the Netmiko driver)

    Returns result dict — never raises.
    """
    result = {
        'success':          False,
        'outputs':          {},
        'output':           '',
        'error':            None,
        'privilege_denied': False,
        'pre_check_failed': False,
        'pre_check_output': '',
    }

    if not _NETMIKO_OK:
        result['error'] = f'netmiko not installed: {_NETMIKO_IMPORT_ERROR}'
        return result

    # Map iAutomate platform classification to the correct Netmiko driver.
    # cisco_ios driver mishandles IOS-XR prompts/config mode, so XR must use cisco_xr.
    _DRIVER_MAP = {'ios': 'cisco_ios', 'ios_xe': 'cisco_ios', 'ios_xr': 'cisco_xr'}
    device_type = _DRIVER_MAP.get(str(platform).strip().lower(), 'cisco_ios')

    device_params = {
        'device_type':   device_type,
        'host':          host,
        'username':      username,
        'password':      password,
        'secret':        password,          # Attempt enable with TACACS password
        'conn_timeout':  CONN_TIMEOUT,
        'auth_timeout':  AUTH_TIMEOUT,
        'banner_timeout': CONN_TIMEOUT,
        'global_delay_factor': 1,
        'fast_cli':      False,
    }

    try:
        conn = ConnectHandler(**device_params)
    except (NetmikoAuthenticationException,) as exc:
        msg = str(exc)
        if _PRIV_DENIED_PATTERNS.search(msg):
            result['privilege_denied'] = True
        result['error'] = f'Authentication failed: {msg}'
        return result
    except (NetmikoTimeoutException, NetMikoTimeoutException, Exception) as exc:
        result['error'] = f'Connection failed: {exc}'
        return result

    try:
        # Attempt to enter enable mode
        try:
            if not conn.check_enable_mode():
                conn.enable()
        except Exception as exc:
            msg = str(exc)
            if _ENABLE_FAILED_PATTERNS.search(msg) or _PRIV_DENIED_PATTERNS.search(msg):
                result['privilege_denied'] = True
                result['error'] = f'Enable mode denied: {msg}'
                conn.disconnect()
                return result
            # Non-auth enable failure — continue without enable (read-only still works)

        # Pre-check gate (bounce safety: verify interface is still down before acting)
        if pre_check and isinstance(pre_check, dict):
            gate_cmd = pre_check.get('command', '')
            must_contain = pre_check.get('must_contain', '')
            if gate_cmd and must_contain:
                gate_output = conn.send_command(gate_cmd, read_timeout=CMD_TIMEOUT)
                result['pre_check_output'] = gate_output
                if must_contain.lower() not in gate_output.lower():
                    result['pre_check_failed'] = True
                    result['success']          = True   # Not an error — pre-check prevented action
                    result['outputs']['_pre_check_gate'] = gate_output
                    conn.disconnect()
                    return result

        # Show commands
        if isinstance(commands, list):
            for cmd in commands:
                try:
                    out = conn.send_command(cmd, read_timeout=CMD_TIMEOUT)
                    result['outputs'][cmd] = out
                except Exception as exc:
                    result['outputs'][cmd] = f'[COMMAND ERROR: {exc}]'
        elif isinstance(commands, str) and commands.strip():
            try:
                out = conn.send_command(commands, read_timeout=CMD_TIMEOUT)
                result['outputs'][commands] = out
                result['output']            = out
            except Exception as exc:
                result['outputs'][commands] = f'[COMMAND ERROR: {exc}]'
                result['error']             = str(exc)

        # Config commands (only reached if pre_check passed or not specified)
        if config_commands and isinstance(config_commands, list):
            try:
                config_out = conn.send_config_set(
                    config_commands,
                    read_timeout=CONFIG_TIMEOUT,
                    exit_config_mode=True,
                )
                result['outputs']['_config_output'] = config_out
            except Exception as exc:
                result['outputs']['_config_error'] = str(exc)
                result['error'] = f'Config command failed: {exc}'

        result['success'] = True

    except Exception as exc:
        result['error'] = f'Execution error: {exc}'
    finally:
        try:
            conn.disconnect()
        except Exception:
            pass

    return result


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    # Optional named token: platform=ios|ios_xe|ios_xr (scanned out of argv so
    # it never disturbs positional ordering; absent → defaults to ios/cisco_ios).
    platform = 'ios'
    argv = []
    for a in sys.argv[1:]:
        if isinstance(a, str) and a.startswith('platform='):
            platform = a.split('=', 1)[1] or 'ios'
        else:
            argv.append(a)

    if len(argv) < 4:
        out = {
            'success':  False,
            'outputs':  {},
            'output':   '',
            'error':    f'Usage: device_ssh.py host user password commands_json [pre_check_json] [config_cmds_json] [platform=...]',
            'privilege_denied': False,
            'pre_check_failed': False,
            'pre_check_output': '',
        }
        print(json.dumps(out))
        sys.exit(0)

    host          = argv[0]
    username      = argv[1]
    password      = argv[2]
    commands_json = argv[3]
    pre_check_json    = argv[4] if len(argv) > 4 else '{}'
    config_cmds_json  = argv[5] if len(argv) > 5 else '[]'

    try:
        commands = json.loads(commands_json)
    except Exception as exc:
        commands = []
        print(json.dumps({
            'success': False, 'outputs': {}, 'output': '',
            'error': f'commands_json parse error: {exc}',
            'privilege_denied': False, 'pre_check_failed': False, 'pre_check_output': '',
        }))
        sys.exit(0)

    try:
        pre_check = json.loads(pre_check_json) if pre_check_json and pre_check_json != '{}' else None
    except Exception:
        pre_check = None

    try:
        config_commands = json.loads(config_cmds_json) if config_cmds_json and config_cmds_json != '[]' else None
    except Exception:
        config_commands = None

    result = _run(host, username, password, commands, pre_check, config_commands, platform)
    print(json.dumps(result))
    sys.exit(0)   # Always 0 — Ansible must never see non-zero from this script


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        # Last-resort guard: emit valid JSON and exit 0 so Ansible never sees
        # a non-zero rc from this helper.
        import json as _json, sys as _sys
        print(_json.dumps({'success': False, 'outputs': {}, 'output': '',
                           'error': 'unhandled exception: %s' % exc}))
        _sys.exit(0)

