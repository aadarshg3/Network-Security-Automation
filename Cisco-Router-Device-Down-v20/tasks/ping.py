#!/usr/bin/env python3
"""
ping.py — iAutomate ICMP ping for Cisco-Router-Device-Down.

Usage:
  python3 ping.py '<host>' [count]

Always exits 0. Errors embedded in JSON stdout.

JSON output:
  {
    "host":        "192.168.31.189",
    "success":     bool,
    "packet_loss": int (0-100),
    "output":      "raw ping output",
    "error":       null | "message"
  }
"""

import sys
import json
import subprocess
import re


def run_ping(host, count=5, timeout=5):
    """Execute ping and return result dict."""
    result = {
        'host':        host,
        'success':     False,
        'packet_loss': 100,
        'output':      '',
        'error':       None,
    }

    try:
        proc = subprocess.run(
            ['ping', '-c', str(count), '-W', str(timeout), host],
            capture_output=True,
            text=True,
            timeout=count * (timeout + 2),
        )
        stdout = proc.stdout
        stderr = proc.stderr
        result['output'] = stdout + stderr

        # Parse packet loss from ping summary line
        # Example: "5 packets transmitted, 5 received, 0% packet loss"
        loss_match = re.search(r'(\d+)%\s+packet\s+loss', stdout)
        if loss_match:
            loss = int(loss_match.group(1))
            result['packet_loss'] = loss
            result['success']     = loss < 100
        elif proc.returncode == 0:
            result['packet_loss'] = 0
            result['success']     = True
        else:
            result['packet_loss'] = 100
            result['success']     = False

    except subprocess.TimeoutExpired:
        result['error']       = f'Ping timed out after {count * (timeout + 2)}s'
        result['packet_loss'] = 100
        result['success']     = False
    except FileNotFoundError:
        result['error']   = 'ping binary not found'
        result['success'] = False
    except Exception as exc:
        result['error']   = str(exc)
        result['success'] = False

    return result


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            'host':        '',
            'success':     False,
            'packet_loss': 100,
            'output':      '',
            'error':       'Usage: ping.py <host> [count]',
        }))
        sys.exit(0)

    host  = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    result = run_ping(host, count)
    print(json.dumps(result))
    sys.exit(0)   # Always 0


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

