#!/usr/bin/env python3
"""
jump_ssh.py — iAutomate two-hop SSH executor for Cisco-Router-Device-Down (v12).

Hop-1: SSH to secondary CE.
Hop-2: from secondary, SSH to primary CE via LAN/VRRP IP.
Runs show commands (and optionally config commands with a pre-check gate)
on the primary.  All remediation-path phases use this script instead of
device_ssh.py, because MgmtIP is unreachable on the secondary-jump path.

Usage:
  python3 jump_ssh.py '<sec_host>' '<sec_user>' '<sec_pw_json>' \
      '<primary_ip>' '<pri_pw_json>' '<commands_json>' \
      ['<pre_check_json>'] ['<config_cmds_json>'] \
      [platform=ios|ios_xe|ios_xr] [expect_hostname=<primary-neid>]

  sec_pw_json / pri_pw_json : JSON arrays of cinfo credential strings.
  commands_json             : JSON list of show/exec commands to run.
  pre_check_json (optional) : {"command":"...", "must_contain":"..."} gate.
                              If condition not met, config_cmds are skipped
                              and result.pre_check_failed = True.
  config_cmds_json (optional): JSON list of config/exec commands to run
                              AFTER show commands (e.g. WAN bounce, BGP clear).
                              Each command is sent individually and awaits the
                              next prompt (works for both exec and config mode).

Always exits 0. JSON on stdout matches device_ssh.py shape so downstream
Ansible tasks (safe_json_parse, precheck_aborted, check_privilege_denied)
work identically regardless of which script was called.
"""

import sys
import json
import re
import time

try:
    from netmiko import ConnectHandler
    _NETMIKO_OK = True
except ImportError as _ie:
    _NETMIKO_OK = False
    _IMPORT_ERR = str(_ie)

_DRIVER_MAP = {'ios': 'cisco_ios', 'ios_xe': 'cisco_ios', 'ios_xr': 'cisco_xr'}

_HOSTKEY_PROMPT = re.compile(r'\(yes/no\)|continue connecting|fingerprint', re.IGNORECASE)
# Password prompt may be followed by a streamed login banner, so do NOT anchor to
# end-of-buffer. Match the prompt anywhere in the freshly-read window.
_PASSWORD_PROMPT = re.compile(r'[Pp]assword:\s*', re.MULTILINE)
_REFUSED        = re.compile(r'[Cc]onnection refused|refused by remote host', re.IGNORECASE)
_NO_ROUTE       = re.compile(r'%?\s*(No route to host|Destination unreachable|Connection timed out|% Connection)', re.IGNORECASE)
# Exec prompt: hostname followed by # or > at end of a line. Allow trailing
# whitespace; the prompt is the last meaningful token on the channel.
_EXEC_PROMPT    = re.compile(r'[\r\n][\w.\-]+[#>]\s*$')
_ANY_PROMPT     = re.compile(r'[\w.\-]+(?:\(config[^\)]*\))?[#>]\s*$')


def _result(**kw):
    base = {
        'success': False, 'outputs': {}, 'output': '', 'error': None,
        'stage': 'secondary_ssh',
        'secondary_login': False, 'jump_attempted': False, 'jump_login': False,
        'connection_refused': False, 'landing_verified': False,
        'primary_ip_used': '', 'detail': '',
        # device_ssh.py compat keys so precheck_aborted / check_privilege_denied work
        'pre_check_failed': False, 'pre_check_output': '', 'privilege_denied': False,
    }
    base.update(kw)
    return base


# ---------------------------------------------------------------------------
# Hop-1: SSH to secondary
# ---------------------------------------------------------------------------

def _try_secondary(sec_host, sec_user, sec_pw_list, platform):
    driver = _DRIVER_MAP.get(str(platform).lower(), 'cisco_ios')
    last_err = None
    for pw in sec_pw_list:
        try:
            conn = ConnectHandler(
                device_type=driver, host=sec_host, username=sec_user,
                password=pw, secret=pw, conn_timeout=30, auth_timeout=30,
                banner_timeout=30, fast_cli=False,
            )
            try:
                conn.enable()
            except Exception:
                pass
            return conn, pw, None
        except Exception as e:
            last_err = f'{type(e).__name__}: {e}'
    return None, None, last_err or 'secondary auth failed (all cinfo creds)'


# ---------------------------------------------------------------------------
# Hop-2: in-session SSH from secondary to primary
# ---------------------------------------------------------------------------

def _prompt_hostname(text):
    """
    Return the hostname of the last exec prompt (e.g. 'R25#' -> 'r25') found
    anywhere in the buffer. Robust to banner lines that follow the prompt.
    """
    if not text:
        return ''
    matches = re.findall(r'(?m)^([\w.\-]+)[#>]\s*$', text)
    if matches:
        return matches[-1].strip().lower()
    # Fallback: last non-empty line ending in # or >
    for line in reversed(text.strip().splitlines()):
        m = re.match(r'^([\w.\-]+)[#>]\s*$', line.strip())
        if m:
            return m.group(1).strip().lower()
    return ''


def _attempt_jump(conn, ssh_cmd, pri_pw_list, secondary_hostname):
    out = {
        'jump_attempted': True, 'jump_login': False, 'connection_refused': False,
        'landing_verified': False, 'detail': '', 'error': None,
    }
    trail = [f'issued: {ssh_cmd}']
    sec_host = str(secondary_hostname).strip().lower()
    creds = list(pri_pw_list)

    # Raw-channel reader. Inside a nested SSH jump the session is NOT
    # Netmiko-managed, so we read the channel directly and accumulate everything
    # the device streams (SSH banner -> Password: -> login banner -> exec prompt),
    # tolerating multi-line banners that arrive in fragments. Under Ansible's
    # no-TTY subprocess the banner/prompt can arrive in bursts, so the reader
    # settles on a short quiet period rather than waiting a fixed window.
    def _read(window):
        """Accumulate channel data up to `window` seconds, returning as soon as
        the stream goes quiet after data arrives."""
        buf = ''
        end = time.time() + window
        idle = 0
        while time.time() < end:
            try:
                chunk = conn.read_channel()
            except Exception:
                chunk = ''
            if chunk:
                buf += chunk
                idle = 0
            else:
                idle += 1
                if buf and idle >= 2:   # ~0.4s quiet after data => settled
                    break
            time.sleep(0.2)
        return buf

    try:
        conn.write_channel(ssh_cmd + '\n')
        buf = ''
        creds_used = 0
        answered_this_buf = False
        empty_reads = 0
        deadline = time.time() + 20
        buf += _read(6)
        while time.time() < deadline:
            new = _read(3)
            buf += new

            if not new:
                empty_reads += 1
                if empty_reads <= 2:
                    conn.write_channel('\n')
                    trail.append(f'channel quiet — nudge #{empty_reads}')
                    buf += _read(3)
            else:
                empty_reads = 0

            if _REFUSED.search(buf):
                out['connection_refused'] = True
                out['detail'] = '; '.join(trail + ['Connection refused by remote host (ACL)'])
                return out
            if _NO_ROUTE.search(buf):
                out['detail'] = '; '.join(trail + ['no route / timeout to primary'])
                return out
            if _HOSTKEY_PROMPT.search(buf):
                conn.write_channel('yes\n')
                trail.append('answered host-key yes')
                buf = ''
                continue

            # Unanswered Password: prompt in the current buffer -> send next cred.
            if _PASSWORD_PROMPT.search(buf) and not answered_this_buf:
                if not creds:
                    out['detail'] = '; '.join(trail + [f'all cinfo creds rejected (tried {creds_used})'])
                    return out
                conn.write_channel(creds.pop(0) + '\n')
                creds_used += 1
                answered_this_buf = True
                trail.append(f'sent cinfo cred #{creds_used} at Password:')
                buf = ''
                continue

            # Evaluate the landing prompt (only meaningful once a cred was sent).
            if creds_used > 0:
                host = _prompt_hostname(buf)
                if host:
                    if sec_host and host == sec_host:
                        # Bounced back to the SECONDARY's own prompt = the
                        # credential we just sent was REJECTED and the nested
                        # ssh dropped us home. Re-issue ssh to try the next
                        # cinfo cred, unless we have none left.
                        if creds:
                            trail.append(f'cred #{creds_used} rejected (returned to secondary {host!r}); retrying next cred')
                            conn.write_channel(ssh_cmd + '\n')
                            buf = ''
                            answered_this_buf = False
                            continue
                        else:
                            out['detail'] = '; '.join(trail + [f'all cinfo creds rejected, returned to secondary {host!r} (tried {creds_used})'])
                            return out
                    else:
                        # An exec prompt that is NOT the secondary = landed on primary.
                        out['jump_login'] = True
                        out['landing_verified'] = True
                        trail.append(f'landed on primary, prompt host {host!r}')
                        out['detail'] = '; '.join(trail)
                        return out

        tail = buf.strip().splitlines()[-1] if buf.strip() else ''
        out['detail'] = '; '.join(trail + [f'no verified exec prompt within timeout (creds_tried={creds_used}, last seen: {tail!r})'])
        return out
    except Exception as e:
        out['error'] = f'jump exception: {type(e).__name__}: {e}'
        out['detail'] = '; '.join(trail + [out['error']])
        return out


def _recover_secondary_prompt(conn):
    try:
        conn.write_channel('\x03\n')
        time.sleep(1.0)
        conn.read_channel()
    except Exception:
        pass


def _jump_to_primary(conn, primary_ip, sec_user, pri_pw_list, secondary_hostname, max_rounds=2):
    # ssh forms to try, in order. The explicit -l form goes first since we always
    # have a username; the bare form is a fallback. No VRF form — no VRF here.
    forms = [
        f'ssh -l {sec_user} {primary_ip}',
        f'ssh {primary_ip}',
    ]
    last = None
    for rnd in range(1, max_rounds + 1):
        for ssh_cmd in forms:
            attempt = _attempt_jump(conn, ssh_cmd, list(pri_pw_list), secondary_hostname)
            last = attempt
            if attempt['jump_login'] and attempt['landing_verified']:
                attempt['detail'] = f'[round {rnd}] ' + attempt['detail']
                return attempt
            # ACL refusal is deterministic — retrying will not change it.
            if attempt['connection_refused']:
                attempt['detail'] = f'[round {rnd}] ' + attempt['detail']
                return attempt
            _recover_secondary_prompt(conn)
        if rnd < max_rounds:
            last['detail'] += f' | round {rnd} failed, retrying jump (round {rnd + 1}/{max_rounds})'
            time.sleep(1)
    if last is not None:
        last['detail'] = f'[{max_rounds} rounds attempted] ' + last['detail']
    return last


# ---------------------------------------------------------------------------
# Run commands on landed primary session
# ---------------------------------------------------------------------------

def _run_on_primary(conn, commands, pre_check=None, config_commands=None):
    """
    Execute show/exec commands on the landed primary session. Netmiko's
    base_prompt must already be re-baselined to the primary by the caller.

    pre_check      : {'command','must_contain'} gate; if unmet, config is skipped
                     and outputs['_pre_check_aborted']='True'.
    config_commands: commands sent after show commands (exec or config mode).
    """
    outputs = {}

    def _send(cmd, timeout):
        # Prefer base_prompt-aware send; fall back to a permissive prompt regex.
        try:
            return conn.send_command(cmd, read_timeout=timeout)
        except Exception:
            return conn.send_command(
                cmd, read_timeout=timeout,
                expect_string=r'[\w.\-]+[#>]\s*$')

    if pre_check and isinstance(pre_check, dict):
        gate_cmd = pre_check.get('command', '')
        must_contain = pre_check.get('must_contain', '')
        if gate_cmd and must_contain:
            try:
                gate_output = _send(gate_cmd, 30)
                outputs['_pre_check_gate'] = gate_output
                if must_contain.lower() not in gate_output.lower():
                    outputs['_pre_check_aborted'] = 'True'
                    return outputs
            except Exception as e:
                outputs['_pre_check_error'] = f'[PRE-CHECK ERROR] {type(e).__name__}: {e}'
                outputs['_pre_check_aborted'] = 'True'
                return outputs

    for cmd in commands:
        try:
            outputs[cmd] = _send(cmd, 45)
        except Exception as e:
            outputs[cmd] = f'[COMMAND ERROR] {type(e).__name__}: {e}'

    if config_commands and isinstance(config_commands, list):
        cfg_lines = []
        for cmd in config_commands:
            try:
                out = conn.send_command(
                    cmd, read_timeout=30,
                    expect_string=r'[\w.\-]+(?:\(config[^\)]*\))?[#>]\s*$')
                cfg_lines.append(f'[{cmd}]\n{out}')
            except Exception as e:
                cfg_lines.append(f'[{cmd}] [ERROR] {type(e).__name__}: {e}')
        outputs['_config_output'] = '\n'.join(cfg_lines)

    return outputs


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    platform = 'ios'
    secondary_hostname = ''
    jump_password_override = ''   # LAB-ONLY: if set, tried first. Empty in prod.
    jump_user_override = ''       # LAB-ONLY: if set, used for the jump ssh -l. Empty in prod.
    argv = []
    for a in sys.argv[1:]:
        if a.startswith('platform='):
            platform = a.split('=', 1)[1] or 'ios'
        elif a.startswith('secondary_hostname='):
            secondary_hostname = a.split('=', 1)[1]
        elif a.startswith('jump_password_override='):
            jump_password_override = a.split('=', 1)[1]
        elif a.startswith('jump_user_override='):
            jump_user_override = a.split('=', 1)[1]
        elif a.startswith('expect_hostname='):
            # back-compat: ignored for landing logic; kept so callers don't break
            pass
        else:
            argv.append(a)

    if not _NETMIKO_OK:
        print(json.dumps(_result(error=f'netmiko import failed: {_IMPORT_ERR}')))
        sys.exit(0)

    if len(argv) < 6:
        print(json.dumps(_result(
            error='Usage: jump_ssh.py sec_host sec_user sec_pw_json primary_ip pri_pw_json '
                  'commands_json [pre_check_json] [config_cmds_json] [platform=] [secondary_hostname=]')))
        sys.exit(0)

    sec_host, sec_user = argv[0], argv[1]
    try:
        sec_pw_list = json.loads(argv[2])
        primary_ip  = argv[3]
        pri_pw_list = json.loads(argv[4])
        commands    = json.loads(argv[5])
    except Exception as e:
        print(json.dumps(_result(error=f'bad JSON arg (positions 2-5): {e}')))
        sys.exit(0)

    # Optional: pre_check (argv[6]) and config_commands (argv[7])
    pre_check = {}
    config_commands = []
    if len(argv) > 6 and argv[6] not in ('{}', ''):
        try:
            pre_check = json.loads(argv[6]) or {}
        except Exception:
            pre_check = {}
    if len(argv) > 7 and argv[7] not in ('[]', ''):
        try:
            config_commands = json.loads(argv[7]) or []
        except Exception:
            config_commands = []

    if isinstance(sec_pw_list, str):
        sec_pw_list = [sec_pw_list]
    if isinstance(pri_pw_list, str):
        pri_pw_list = [pri_pw_list]

    # LAB-ONLY override: if jump_password_override is set, try it FIRST, then
    # fall back to the cinfo creds. Defaults empty -> no effect in prod. Never
    # set this extra-var in production; it exists only for SIT/lab where the
    # device password differs from the cinfo credential set.
    if jump_password_override:
        pri_pw_list = [jump_password_override] + [
            p for p in pri_pw_list if p != jump_password_override
        ]

    # LAB-ONLY: the jump ssh username. In prod this is the same TACACS user used
    # for the secondary (sec_user). In the lab the devices use a local user
    # (e.g. 'cisco') that differs from the prod TACACS user, so jump_user_override
    # lets the lab target the right account without affecting prod. Empty default.
    jump_user = jump_user_override or sec_user

    res = _result(primary_ip_used=primary_ip)

    # Hop-1: SSH to secondary
    conn, _sec_pw, err = _try_secondary(sec_host, sec_user, sec_pw_list, platform)
    if not conn:
        res['error'] = f'secondary SSH failed: {err}'
        res['stage'] = 'secondary_ssh'
        print(json.dumps(res))
        sys.exit(0)
    res['secondary_login'] = True
    res['stage'] = 'vrrp_jump'

    if not secondary_hostname:
        try:
            secondary_hostname = _prompt_hostname(conn.find_prompt())
        except Exception:
            secondary_hostname = ''

    jump = _jump_to_primary(conn, primary_ip, jump_user, pri_pw_list, secondary_hostname)
    res.update({k: jump[k] for k in
                ('jump_attempted', 'jump_login', 'connection_refused',
                 'landing_verified', 'detail')})
    if jump.get('error'):
        res['error'] = jump['error']

    if not (jump['jump_login'] and jump['landing_verified']):
        try:
            conn.disconnect()
        except Exception:
            pass
        print(json.dumps(res))
        sys.exit(0)

    # Landed and verified — run commands on primary
    res['stage'] = 'landed'

    # The jump was done over the raw channel, so Netmiko's base_prompt still
    # reflects the SECONDARY. Re-baseline to the primary and disable paging on
    # the primary itself, otherwise send_command mismatches the prompt and long
    # outputs stall at --More--.
    try:
        conn.set_base_prompt()
    except Exception:
        pass
    try:
        conn.write_channel('terminal length 0\n')
        time.sleep(1.0)
        conn.read_channel()
    except Exception:
        pass
    try:
        conn.set_base_prompt()
    except Exception:
        pass

    outputs = _run_on_primary(conn, commands, pre_check, config_commands)
    res['outputs'] = outputs
    # Pre-check compat: set pre_check_failed if the gate aborted
    if '_pre_check_aborted' in outputs:
        res['pre_check_failed'] = True
    res['success'] = True
    res['stage'] = 'done'

    try:
        conn.disconnect()
    except Exception:
        pass

    print(json.dumps(res))
    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        import json as _j, sys as _s
        print(_j.dumps({'success': False, 'outputs': {}, 'output': '',
                        'error': f'unhandled exception: {exc}',
                        'pre_check_failed': False, 'privilege_denied': False}))
        _s.exit(0)
