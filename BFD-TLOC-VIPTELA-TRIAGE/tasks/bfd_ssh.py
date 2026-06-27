#!/usr/bin/env python3
import sys
import json
import re
import os
from hashlib import md5

try:
    from netmiko import ConnectHandler
    from netmiko import NetmikoTimeoutException
    import paramiko
except ImportError as e:
    print(json.dumps({"failed": True, "msg": f"Import error: {e}"}))
    sys.exit(1)

md5_bypass = False

def bypass_md5(device):
    orig = md5.__init__
    def new_init(self, *args, **kwargs):
        kwargs['usedforsecurity'] = False
        orig(self, *args, **kwargs)
    md5.__init__ = new_init

def ssh_connect(device):
    global md5_bypass
    try:
        conn = ConnectHandler(**device)
        return conn, True, "OK"
    except paramiko.AuthenticationException as e:
        return None, False, f"Auth failed: {e}"
    except ValueError as e:
        if not md5_bypass:
            bypass_md5(device)
            md5_bypass = True
            return ssh_connect(device)
        return None, False, f"ValueError: {e}"
    except Exception as e:
        return None, False, str(e)

def run_commands(conn, commands):
    output = {}
    for cmd in commands:
        try:
            output[cmd] = conn.send_command(cmd, read_timeout=60)
        except Exception as e:
            output[cmd] = f"ERROR: {e}"
    return output

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"failed": True, "msg": "No args"}))
        sys.exit(1)

    try:
        args = json.loads(sys.argv[1])
    except Exception as e:
        print(json.dumps({"failed": True, "msg": f"Args parse error: {e}"}))
        sys.exit(1)

    host = args.get("host")
    username = args.get("username")
    password = args.get("password")
    enable = args.get("enable_password", "")
    commands = args.get("commands", [])
    config_commands = args.get("config_commands", [])
    device_type = args.get("device_type", "cisco_ios")

    device = {
        "device_type": device_type,
        "host": host,
        "username": username,
        "password": password,
        "timeout": 60,
        "global_delay_factor": 2,
    }
    if enable:
        device["secret"] = enable

    conn, ok, msg = ssh_connect(device)
    if not ok:
        print(json.dumps({"failed": True, "msg": msg, "output": {}}))
        sys.exit(0)

    try:
        if enable:
            try:
                conn.enable()
            except Exception:
                pass

        output = {}
        if commands:
            output = run_commands(conn, commands)

        if config_commands:
            try:
                cfg_out = conn.send_config_set(config_commands)
                output["config"] = cfg_out
                conn.save_config()
            except Exception as e:
                output["config"] = f"ERROR: {e}"

        conn.disconnect()
        print(json.dumps({"failed": False, "msg": "OK", "output": output}))
    except Exception as e:
        print(json.dumps({"failed": True, "msg": str(e), "output": {}}))

if __name__ == "__main__":
    main()
