#!/usr/bin/env python3
"""
sec_to_pri_login.py - v53 secondary -> primary LAN-side login ladder.

SELF-CONTAINED by design: run exactly like device_ssh.py / jump_ssh.py via the
Ansible `script` module (single file copied to a temp dir and executed), so it
depends on NO sibling import and NO role_path. The hop-1/hop-2 helpers below are
adapted from the prod-proven jump_ssh.py; jump_ssh.py itself is NOT modified.

WHAT IT ADDS over the MOP VIP jump (jump_ssh.py, live, untouched):
  per-site, zero-assumption login to the primary's REAL LAN IP -
    1. SSH, VRF-aware ONLY when a VRF name is supplied (detected upstream),
    2. if SSH fails/refused, fall back to TELNET (same VRF-awareness),
  choosing the protocol by what actually works on THIS device.

USAGE (ansible.builtin.script, secrets on STDIN - never argv):
  python3 sec_to_pri_login.py <sec_host> <sec_user> <primary_lan_ip> \
      [vrf=<name>] [allow_telnet=0|1] [platform=ios|ios_xe|ios_xr] \
      [secondary_hostname=<neid>]
  STDIN (JSON):  {"sec_pw":[...], "pri_pw":[...], "commands":[...]}
    *_pw entries are role-tagged {user,pass,role,preferred} (or bare strings),
    from resolve_login_chain - CINFO only; this script invents no credential.

SECURITY: never logs a secret VALUE (records 'sent password at Password:' only);
secrets arrive on stdin so they never appear in `ps`. Always exits 0; JSON on
stdout in the jump_ssh.py result shape plus 'method' (ssh|telnet|none) and 'vrf'.
Python 3.12. No telnet library on the controller - telnet is driven inside the
secondary's netmiko channel.
"""

import os
import sys
import json
import re
import time
import signal

try:
    from netmiko import ConnectHandler
    _NETMIKO_OK = True
    _IMPORT_ERR = ''
except ImportError as _ie:
    _NETMIKO_OK = False
    _IMPORT_ERR = str(_ie)

_DRIVER_MAP = {'ios': 'cisco_ios', 'ios_xe': 'cisco_ios', 'ios_xr': 'cisco_xr'}

_HOSTKEY_PROMPT = re.compile(r'\(yes/no\)|continue connecting|fingerprint', re.IGNORECASE)
_PASSWORD_PROMPT = re.compile(r'[Pp]assword:\s*', re.MULTILINE)
_USERNAME_PROMPT = re.compile(r'[Uu]sername:\s*', re.MULTILINE)
_REFUSED = re.compile(r'[Cc]onnection refused|refused by remote host', re.IGNORECASE)
_NO_ROUTE = re.compile(r'%?\s*(No route to host|Destination unreachable|Connection timed out|% Connection)', re.IGNORECASE)

_LOGIN_ROLES = ('tacacs', 'local', 'login')


# ---------------------------------------------------------------------------
# Credential handling (adapted verbatim from jump_ssh.py)
# ---------------------------------------------------------------------------
def _norm_creds(raw, default_user):
    out = []
    if isinstance(raw, str):
        raw = [raw]
    for item in (raw or []):
        if isinstance(item, dict):
            role = str(item.get('role') or 'login')
            pw = item.get('pass')
            user = (item.get('user') or '') if role in ('enable', 'enable_fallback') \
                else (item.get('user') or default_user)
            if pw:
                out.append({'user': user, 'pass': pw, 'role': role,
                            'preferred': bool(item.get('preferred'))})
        elif item:
            out.append({'user': default_user, 'pass': item, 'role': 'login', 'preferred': False})
    return out


def _secondary_login_creds(creds):
    tac = [c for c in creds if c['role'] == 'tacacs']
    return tac if tac else [c for c in creds if c['role'] in _LOGIN_ROLES]


def _primary_login_creds(creds):
    logins = [c for c in creds if c['role'] in _LOGIN_ROLES]
    if any(c['role'] in ('local', 'tacacs') for c in logins):
        rank = {'local': 0, 'tacacs': 1, 'login': 2}
        logins = sorted(logins, key=lambda c: (0 if c.get('preferred') else 1, rank.get(c['role'], 3)))
    out, seen = [], set()
    for c in logins:
        key = (c['user'], c['pass'])
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out


def _enable_secrets(creds):
    rank = {'enable': 0, 'enable_fallback': 1, 'local': 2, 'tacacs': 3, 'login': 4}
    out, seen = [], set()
    for c in sorted(creds, key=lambda c: rank.get(c['role'], 5)):
        if c['pass'] not in seen:
            seen.add(c['pass'])
            out.append(c['pass'])
    return out


def _try_secondary(sec_host, sec_creds, platform):
    driver = _DRIVER_MAP.get(str(platform).lower(), 'cisco_ios')
    last_err = None
    for c in sec_creds:
        try:
            conn = ConnectHandler(
                device_type=driver, host=sec_host, username=c['user'],
                password=c['pass'], secret=c['pass'], conn_timeout=30, auth_timeout=30,
                banner_timeout=30, fast_cli=False,
            )
            try:
                conn.enable()
            except Exception:
                pass
            return conn, c['user'], c['pass'], None
        except Exception as e:
            last_err = '%s: %s' % (type(e).__name__, e)
    return None, None, None, last_err or 'secondary auth failed (all credentials)'


def _prompt_hostname(text):
    if not text:
        return ''
    matches = re.findall(r'(?m)^([\w.\-]+)[#>]\s*$', text)
    if matches:
        return matches[-1].strip().lower()
    for line in reversed(text.strip().splitlines()):
        m = re.match(r'^([\w.\-]+)[#>]\s*$', line.strip())
        if m:
            return m.group(1).strip().lower()
    return ''


def _read_channel(conn, window):
    """Accumulate channel data up to `window` s, return once it goes quiet after
    data arrives."""
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
            if buf and idle >= 2:
                break
        time.sleep(0.2)
    return buf


def _flush(conn):
    try:
        conn.read_channel()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Hop-2 SSH attempt (adapted verbatim from jump_ssh._attempt_jump)
# ---------------------------------------------------------------------------
def _attempt_ssh_jump(conn, ssh_cmd, password, secondary_hostname, deadline_s=25):
    out = {'jump_attempted': True, 'jump_login': False, 'connection_refused': False,
           'landing_verified': False, 'detail': '', 'error': None,
           'auth_failed': False, 'no_route': False, 'password_sent': False}
    trail = ['issued: %s' % ssh_cmd]
    sec_host = str(secondary_hostname).strip().lower()
    try:
        _flush(conn)
        conn.write_channel(ssh_cmd + '\n')
        buf = _read_channel(conn, 6)
        nudged = False
        deadline = time.time() + deadline_s
        while True:
            if _REFUSED.search(buf):
                out['connection_refused'] = True
                out['detail'] = '; '.join(trail + ['Connection refused by remote host'])
                return out
            if _NO_ROUTE.search(buf):
                out['no_route'] = True
                out['detail'] = '; '.join(trail + ['no route / timeout to primary'])
                return out
            if _HOSTKEY_PROMPT.search(buf):
                conn.write_channel('yes\n')
                trail.append('answered host-key yes')
                buf = ''
            elif _PASSWORD_PROMPT.search(buf):
                if not out['password_sent']:
                    conn.write_channel(password + '\n')
                    out['password_sent'] = True
                    trail.append('sent password at Password:')
                    buf = ''
                else:
                    out['auth_failed'] = True
                    out['detail'] = '; '.join(trail + ['login rejected (Password: prompted again)'])
                    return out
            elif out['password_sent']:
                host = _prompt_hostname(buf)
                if host:
                    if sec_host and host == sec_host:
                        out['auth_failed'] = True
                        out['detail'] = '; '.join(trail + ['login rejected, returned to secondary %r' % host])
                        return out
                    out['jump_login'] = True
                    out['landing_verified'] = True
                    trail.append('landed on primary, prompt host %r' % host)
                    out['detail'] = '; '.join(trail)
                    return out
            if time.time() >= deadline:
                break
            new = _read_channel(conn, 3)
            buf += new
            if (not new and not nudged and out['password_sent'] and buf.strip()
                    and not _PASSWORD_PROMPT.search(buf) and not _prompt_hostname(buf)):
                conn.write_channel('\n')
                nudged = True
                trail.append('banner received, prompt not shown - one Enter sent')
                buf += _read_channel(conn, 3)
        tail = buf.strip().splitlines()[-1] if buf.strip() else ''
        out['detail'] = '; '.join(trail + ['no verified exec prompt within %ss (last: %r)' % (deadline_s, tail)])
        return out
    except Exception as e:
        out['error'] = 'ssh exception: %s: %s' % (type(e).__name__, e)
        out['detail'] = '; '.join(trail + [out['error']])
        return out


def _attempt_telnet_jump(conn, telnet_cmd, user, password, secondary_hostname, deadline_s=30):
    """Telnet login attempt from the secondary. Adds the Username: step over the
    SSH flow. One username + one password (login-block safe). Never logs the
    secret value."""
    out = {'jump_attempted': True, 'jump_login': False, 'connection_refused': False,
           'landing_verified': False, 'detail': '', 'error': None,
           'auth_failed': False, 'no_route': False,
           'username_sent': False, 'password_sent': False}
    trail = ['issued: %s' % telnet_cmd]
    sec_host = str(secondary_hostname).strip().lower()
    try:
        _flush(conn)          # clear any residual (e.g. prompt from a prior refused ssh)
        conn.write_channel(telnet_cmd + '\n')
        buf = _read_channel(conn, 6)
        nudged = False
        deadline = time.time() + deadline_s
        while True:
            if _REFUSED.search(buf):
                out['connection_refused'] = True
                out['detail'] = '; '.join(trail + ['connection refused by remote host'])
                return out
            if _NO_ROUTE.search(buf):
                out['no_route'] = True
                out['detail'] = '; '.join(trail + ['no route / timeout to primary'])
                return out
            if _USERNAME_PROMPT.search(buf) and out['password_sent']:
                out['auth_failed'] = True
                out['detail'] = '; '.join(trail + ['login rejected (Username: prompted again after auth)'])
                return out
            if _USERNAME_PROMPT.search(buf) and not out['username_sent']:
                conn.write_channel(user + '\n')
                out['username_sent'] = True
                trail.append('sent username at Username:')
                buf = ''
            elif _PASSWORD_PROMPT.search(buf):
                if not out['password_sent']:
                    conn.write_channel(password + '\n')
                    out['password_sent'] = True
                    trail.append('sent password at Password:')
                    buf = ''
                else:
                    out['auth_failed'] = True
                    out['detail'] = '; '.join(trail + ['login rejected (Password: prompted again)'])
                    return out
            elif out['password_sent']:
                host = _prompt_hostname(buf)
                if host:
                    if sec_host and host == sec_host:
                        out['auth_failed'] = True
                        out['detail'] = '; '.join(trail + ['login rejected, returned to secondary %r' % host])
                        return out
                    out['jump_login'] = True
                    out['landing_verified'] = True
                    trail.append('landed on primary via telnet, prompt host %r' % host)
                    out['detail'] = '; '.join(trail)
                    return out
            if time.time() >= deadline:
                break
            new = _read_channel(conn, 3)
            buf += new
            if (not new and not nudged and out['username_sent'] and buf.strip()
                    and not _USERNAME_PROMPT.search(buf)
                    and not _PASSWORD_PROMPT.search(buf)
                    and not _prompt_hostname(buf)):
                conn.write_channel('\n')
                nudged = True
                trail.append('banner received, prompt not shown - one Enter sent')
                buf += _read_channel(conn, 3)
        tail = buf.strip().splitlines()[-1] if buf.strip() else ''
        out['detail'] = '; '.join(trail + ['no verified exec prompt within %ss (last: %r)' % (deadline_s, tail)])
        return out
    except Exception as e:
        out['error'] = 'telnet exception: %s: %s' % (type(e).__name__, e)
        out['detail'] = '; '.join(trail + [out['error']])
        return out


# ---------------------------------------------------------------------------
# Enable + run commands (adapted verbatim from jump_ssh.py)
# ---------------------------------------------------------------------------
def _enable_on_primary(conn, enable_pw_list):
    enable_re = re.compile(r'[\w.\-]+#\s*$')

    def _rd(window):
        return _read_channel(conn, window)

    conn.write_channel('\n')
    if enable_re.search(_rd(3)):
        return True
    remaining = list(enable_pw_list or [])
    while remaining:
        conn.write_channel('enable\n')
        buf = _rd(3)
        if enable_re.search(buf):
            return True
        if not _PASSWORD_PROMPT.search(buf):
            break
        while remaining and _PASSWORD_PROMPT.search(buf):
            conn.write_channel(remaining.pop(0) + '\n')
            buf = _rd(3)
            if enable_re.search(buf):
                return True
        if _PASSWORD_PROMPT.search(buf):
            conn.write_channel('\x03')
            _rd(2)
            break
    conn.write_channel('\n')
    return bool(enable_re.search(_rd(3)))


def _run_on_primary(conn, commands):
    outputs = {}

    def _send(cmd, timeout):
        try:
            return conn.send_command(cmd, read_timeout=timeout)
        except Exception:
            return conn.send_command(cmd, read_timeout=timeout,
                                     expect_string=r'[\w.\-]+[#>]\s*$')
    for cmd in commands:
        try:
            outputs[cmd] = _send(cmd, 45)
        except Exception as e:
            outputs[cmd] = '[COMMAND ERROR] %s: %s' % (type(e).__name__, e)
    return outputs


# ---------------------------------------------------------------------------
# Ladder + command construction
# ---------------------------------------------------------------------------
def _ssh_cmd(vrf, user, ip):
    return ('ssh -vrf %s -l %s %s' % (vrf, user, ip)) if vrf else ('ssh -l %s %s' % (user, ip))


def _telnet_cmd(vrf, ip):
    return ('telnet %s /vrf %s' % (ip, vrf)) if vrf else ('telnet %s' % ip)


def _outcome(a):
    if a.get('jump_login') and a.get('landing_verified'):
        return 'landed'
    if a.get('connection_refused'):
        return 'refused'
    if a.get('auth_failed'):
        return 'auth_failed'
    if a.get('no_route'):
        return 'no_route'
    if a.get('error'):
        return 'error'
    return 'no_exec_prompt'


def run_login_ladder(get_conn, pri_login, primary_ip, vrf, allow_telnet,
                     sec_hostname, max_failed=2):
    """SSH (VRF-aware) across the primary login creds; if none land AND telnet is
    enabled, try TELNET. Each credential attempt uses a FRESH secondary session.
    `failed` is shared across BOTH protocols and capped at max_failed, so total
    rejected logins stay below IOS 'login block-for ... attempts 3'. get_conn()
    returns a connected secondary conn or None. Dependency-injected for testing.
    Returns {landed, method, failed, history, conn}."""
    history = []
    state = {'conn': None, 'failed': 0}

    def _ladder(kind):
        for i, cred in enumerate(pri_login):
            if state['conn'] is None:
                state['conn'] = get_conn()
                if state['conn'] is None:
                    history.append('%s: secondary re-login failed' % kind)
                    return None
            conn = state['conn']
            if kind == 'ssh':
                attempt = _attempt_ssh_jump(conn, _ssh_cmd(vrf, cred['user'], primary_ip),
                                            cred['pass'], sec_hostname)
            else:
                attempt = _attempt_telnet_jump(conn, _telnet_cmd(vrf, primary_ip),
                                               cred['user'], cred['pass'], sec_hostname)
            attempt['login_user'] = cred['user']
            attempt['login_role'] = cred['role']
            history.append('%s #%d user=%s role=%s -> %s'
                           % (kind, i + 1, cred['user'], cred['role'], _outcome(attempt)))
            if attempt.get('jump_login') and attempt.get('landing_verified'):
                return attempt
            if attempt.get('connection_refused') or attempt.get('no_route'):
                return None       # deterministic for this protocol; not a failed login
            if attempt.get('password_sent'):
                state['failed'] += 1
            try:
                conn.disconnect()
            except Exception:
                pass
            state['conn'] = None
            if state['failed'] >= max_failed:
                history.append('%s: stopped after %d rejected logins (login-block safe)'
                               % (kind, state['failed']))
                return None
        return None

    landed = _ladder('ssh')
    method = 'ssh' if landed else 'none'
    if not landed and allow_telnet and state['failed'] < max_failed:
        if state['conn'] is None:
            state['conn'] = get_conn()
        landed = _ladder('telnet')
        if landed:
            method = 'telnet'
    return {'landed': landed, 'method': method, 'failed': state['failed'],
            'history': history, 'conn': state['conn']}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
HARD_TIMEOUT = 150
_LAST = None


def _emit_and_exit(res):
    try:
        print(json.dumps(res))
    except Exception:
        print(json.dumps({'success': False, 'method': 'none',
                          'error': 'serialize failure', 'outputs': {}}))
    sys.stdout.flush()
    os._exit(0)


def _on_timeout(signum, frame):
    res = _LAST if isinstance(_LAST, dict) else {'success': False, 'outputs': {}}
    res['error'] = ('hard timeout after %ss - ' % HARD_TIMEOUT) + str(res.get('error') or 'no response')
    _emit_and_exit(res)


def _parse_args(argv):
    opts = {'vrf': '', 'allow_telnet': False, 'platform': 'ios', 'secondary_hostname': ''}
    pos = []
    for a in argv:
        if a.startswith('vrf='):
            opts['vrf'] = a.split('=', 1)[1].strip()
        elif a.startswith('allow_telnet='):
            opts['allow_telnet'] = a.split('=', 1)[1].strip() in ('1', 'true', 'True', 'yes')
        elif a.startswith('platform='):
            opts['platform'] = a.split('=', 1)[1] or 'ios'
        elif a.startswith('secondary_hostname='):
            opts['secondary_hostname'] = a.split('=', 1)[1]
        else:
            pos.append(a)
    return pos, opts


def main():
    pos, opts = _parse_args(sys.argv[1:])
    res = {'success': False, 'method': 'none', 'vrf': opts['vrf'],
           'outputs': {}, 'output': '', 'error': None, 'stage': 'start',
           'secondary_login': False, 'jump_attempted': False, 'jump_login': False,
           'connection_refused': False, 'landing_verified': False, 'enable_mode': False,
           'auth_failed': False, 'no_route': False, 'login_user': '', 'login_role': '',
           'failed_logins': 0, 'primary_ip_used': pos[2] if len(pos) > 2 else '',
           'detail': '', 'pre_check_failed': False, 'privilege_denied': False}
    global _LAST
    _LAST = res
    if hasattr(signal, 'SIGALRM'):
        try:
            signal.signal(signal.SIGALRM, _on_timeout)
            signal.alarm(HARD_TIMEOUT)
        except Exception:
            pass

    if not _NETMIKO_OK:
        res['error'] = 'netmiko import failed: %s' % _IMPORT_ERR
        _emit_and_exit(res)
    if len(pos) < 3:
        res['error'] = ('Usage: sec_to_pri_login.py <sec_host> <sec_user> <primary_lan_ip> '
                        '[vrf=] [allow_telnet=0|1] [platform=] [secondary_hostname=] (creds on stdin)')
        _emit_and_exit(res)
    sec_host, sec_user, primary_ip = pos[0], pos[1], pos[2]

    try:
        bundle = json.loads(sys.stdin.read() or '{}')
    except Exception as e:
        res['error'] = 'bad stdin creds JSON: %s' % e
        _emit_and_exit(res)
    sec_pw_list = bundle.get('sec_pw', [])
    pri_pw_list = bundle.get('pri_pw', [])
    commands = bundle.get('commands', [])

    sec_creds = _secondary_login_creds(_norm_creds(sec_pw_list, sec_user))
    all_pri = _norm_creds(pri_pw_list, sec_user)
    pri_login = _primary_login_creds(all_pri)
    enable_pw_list = _enable_secrets(all_pri)
    if not pri_login:
        res['error'] = 'no login credential for the primary (cinfo login missing)'
        _emit_and_exit(res)

    conn, _u, _p, err = _try_secondary(sec_host, sec_creds, opts['platform'])
    if not conn:
        res['error'] = 'secondary SSH failed: %s' % err
        res['stage'] = 'secondary_ssh'
        _emit_and_exit(res)
    res['secondary_login'] = True
    res['stage'] = 'lan_login'
    sec_hostname = opts['secondary_hostname']
    try:
        live = _prompt_hostname(conn.find_prompt())
        if live:
            sec_hostname = live
    except Exception:
        pass

    _first = {'conn': conn}

    def _get_conn():
        if _first['conn'] is not None:
            c = _first['conn']
            _first['conn'] = None
            return c
        c, _a, _b, _e = _try_secondary(sec_host, sec_creds, opts['platform'])
        return c

    lad = run_login_ladder(_get_conn, pri_login, primary_ip, opts['vrf'],
                           opts['allow_telnet'], sec_hostname)
    landed = lad['landed']
    conn = lad['conn']
    res['method'] = lad['method'] if landed else 'none'
    res['failed_logins'] = lad['failed']
    res['detail'] = 'ladder: ' + ' | '.join(lad['history'])

    if not landed:
        res['jump_attempted'] = True
        try:
            if conn is not None:
                conn.disconnect()
        except Exception:
            pass
        _emit_and_exit(res)

    res['jump_attempted'] = True
    res['jump_login'] = True
    res['landing_verified'] = True
    res['login_user'] = landed.get('login_user', '')
    res['login_role'] = landed.get('login_role', '')
    res['stage'] = 'landed'
    for _fn in (lambda: conn.set_base_prompt(),
                lambda: (conn.write_channel('terminal length 0\n'), time.sleep(1.0), conn.read_channel()),
                lambda: conn.set_base_prompt()):
        try:
            _fn()
        except Exception:
            pass
    res['enable_mode'] = _enable_on_primary(conn, enable_pw_list)
    try:
        conn.set_base_prompt()
    except Exception:
        pass
    res['outputs'] = _run_on_primary(conn, commands)
    res['success'] = True
    res['stage'] = 'done'
    try:
        conn.disconnect()
    except Exception:
        pass
    if hasattr(signal, 'SIGALRM'):
        try:
            signal.alarm(0)
        except Exception:
            pass
    _emit_and_exit(res)


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        print(json.dumps({'success': False, 'method': 'none', 'outputs': {},
                          'error': 'unhandled: %s' % exc,
                          'pre_check_failed': False, 'privilege_denied': False}))
        sys.exit(0)
