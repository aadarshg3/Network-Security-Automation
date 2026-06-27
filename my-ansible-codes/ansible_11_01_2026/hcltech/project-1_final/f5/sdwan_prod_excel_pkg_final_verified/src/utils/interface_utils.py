"""
src/utils/interface_utils.py

Interface name utilities for SD-WAN automation.
Handles the physical-to-logical (sub-interface) port conversion required by UC3.
"""

from __future__ import annotations

import re
from typing import Optional


# Canonical abbreviation map: customer input → normalised prefix
_ABBREV_MAP = {
    "gig":    "GigabitEthernet",
    "gi":     "GigabitEthernet",
    "te":     "TenGigabitEthernet",
    "tengig": "TenGigabitEthernet",
    "eth":    "Ethernet",
    "lo":     "Loopback",
    "tun":    "Tunnel",
}

_INTF_RE = re.compile(
    r"^(?P<prefix>[A-Za-z]+)(?P<path>[\d/]+)(?:\.(?P<vlan>\d+))?$"
)


def to_logical(physical: str, vlan: int) -> str:
    """
    Convert a physical interface name to a sub-interface name.

    Examples:
        to_logical("GigabitEthernet0/0/1", 50) → "GigabitEthernet0/0/1.50"
        to_logical("gig0/0/0", 100)            → "GigabitEthernet0/0/0.100"

    As per customer requirement:
        "edit the variable as Physical port ID to logical port ID.
         For example, gig0/0/0 to gig0/0/0.50"
    """
    normalised = normalise(physical)
    if "." in normalised:
        # Already a sub-interface — update VLAN suffix
        base = normalised.split(".")[0]
        return f"{base}.{vlan}"
    return f"{normalised}.{vlan}"


def normalise(name: str) -> str:
    """
    Normalise an interface name to its canonical form.
    Handles common abbreviations used in customer data.
    """
    name = name.strip()
    m = _INTF_RE.match(name)
    if not m:
        return name  # Return as-is if pattern doesn't match

    prefix = m.group("prefix").lower()
    path   = m.group("path")
    vlan   = m.group("vlan")

    canonical_prefix = _ABBREV_MAP.get(prefix, m.group("prefix"))
    base = f"{canonical_prefix}{path}"
    return f"{base}.{vlan}" if vlan else base


def is_subinterface(name: str) -> bool:
    """Return True if the interface name represents a sub-interface (has a VLAN suffix)."""
    return "." in name.strip()


def strip_vlan(name: str) -> str:
    """Return the base interface name without sub-interface suffix."""
    return name.split(".")[0] if "." in name else name


def extract_vlan(name: str) -> Optional[int]:
    """Extract the VLAN ID from a sub-interface name. Returns None if not a sub-interface."""
    parts = name.split(".")
    if len(parts) == 2:
        try:
            return int(parts[1])
        except ValueError:
            pass
    return None
