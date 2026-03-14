"""
src/utils/logger.py

Logging configuration for SD-WAN automation.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime


def setup_logging(
    level: str = "INFO",
    logs_dir: str = "logs",
    fmt: str = "%(asctime)s  %(levelname)-8s  %(name)s - %(message)s",
) -> str:
    """
    Configure root logging with console + file handlers.
    Returns the log file path.
    """
    os.makedirs(logs_dir, exist_ok=True)
    ts       = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"sdwan_{ts}.log")

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=fmt,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )
    return log_file
