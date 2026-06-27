import json
import logging
import os
from datetime import datetime

logger = logging.getLogger("sdwan.state")

STATE_FILE = "sdwan_state.json"


def _load():
    if not os.path.isfile(STATE_FILE):
        return {}
    with open(STATE_FILE) as f:
        return json.load(f)


def _save(data):
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def is_done(key):
    data = _load()
    entry = data.get(key)
    if entry and entry.get("status") == "deployed":
        return True, entry
    return False, None


def mark_done(key, template_id, device_uuid):
    data = _load()
    data[key] = {
        "status":      "deployed",
        "template_id": template_id,
        "device_uuid": device_uuid,
        "deployed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    _save(data)
    logger.info(f"State marked deployed: {key}")


def show_all():
    data = _load()
    if not data:
        print("  No deployments recorded.")
        return
    for key, val in data.items():
        print(f"  {key}: {val.get('status')}  deployed_at={val.get('deployed_at')}  template={val.get('template_id', '')[:16]}...")
