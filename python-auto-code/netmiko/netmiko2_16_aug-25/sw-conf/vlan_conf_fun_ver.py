import os
import yaml
from getpass import getpass
from concurrent.futures import ThreadPoolExecutor, as_completed
from netmiko import ConnectHandler
from jinja2 import Environment, FileSystemLoader

# ---- Load inventory (hosts only) ----
with open("inventory.yaml") as f:
    inventory = yaml.safe_load(f)["devices"]

# ---- VLANs to deploy ----
VLAN_LIST = [
    {"id": 10, "name": "SALES"},
    {"id": 20, "name": "MKT"},
    {"id": 30, "name": "FINANCE"},
]

# ---- Jinja2 template render -> commands list ----
env = Environment(loader=FileSystemLoader("."))
template = env.get_template("vlans.j2")
rendered = template.render(vlans=VLAN_LIST)
commands = [line for line in (rendered.strip().splitlines()) if line.strip()]

# ---- Credentials: ENV first, prompt if absent ----
USERNAME = os.environ.get("NET_USERNAME") or input("Username: ")
PASSWORD = os.environ.get("NET_PASSWORD") or getpass("Password: ")
ENABLE_SECRET = os.environ.get("NET_ENABLE_SECRET")  # optional
SSH_KEYFILE = os.environ.get("NET_SSH_KEYFILE")      # optional path to private key

def deploy(dev):
    params = {
        "device_type": dev["device_type"],
        "host": dev["host"],
        "username": USERNAME,
        "fast_cli": True,
    }
    if SSH_KEYFILE:
        params.update({"use_keys": True, "key_file": SSH_KEYFILE})
    else:
        params["password"] = PASSWORD
    if ENABLE_SECRET:
        params["secret"] = ENABLE_SECRET

    conn = None
    try:
        conn = ConnectHandler(**params)
        if ENABLE_SECRET:
            conn.enable()
        output = conn.send_config_set(commands)
        # Save config using platform-native method
        try:
            conn.save_config()
        except Exception:
            # Fallback if save_config isn't implemented
            conn.exit_config_mode()
            conn.send_command_timing("write memory")
        return (dev["name"], dev["host"], True, output)
    except Exception as e:
        return (dev["name"], dev["host"], False, str(e))
    finally:
        if conn:
            conn.disconnect()

def main():
    results = []
    with ThreadPoolExecutor(max_workers=min(8, len(inventory))) as pool:
        futures = {pool.submit(deploy, dev): dev for dev in inventory}
        for fut in as_completed(futures):
            results.append(fut.result())

    for name, host, ok, out in results:
        header = f"===== {name} ({host}) ====="
        print(header)
        print(out if ok else f"ERROR: {out}")

if __name__ == "__main__":
    main()

