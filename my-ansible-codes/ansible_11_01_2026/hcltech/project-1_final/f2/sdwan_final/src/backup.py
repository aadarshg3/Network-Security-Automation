import json
import logging
import os
from datetime import datetime

logger = logging.getLogger("sdwan.backup")


def save(label, template_id, data, backup_dir="backups"):
    os.makedirs(backup_dir, exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(backup_dir, f"{ts}_{label}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Backup saved: {path}  template={template_id[:8]}...")
    return path


def load(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Backup not found: {path}")
    with open(path) as f:
        return json.load(f)
