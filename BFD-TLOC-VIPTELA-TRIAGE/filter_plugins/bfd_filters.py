"""Filter plugins for BFD-TLOC-VIPTELA-TRIAGE playbook."""
import re
import logging
from datetime import datetime, timedelta

log = logging.getLogger(__name__)


class FilterModule:
    """Ansible filter plugin for BFD-TLOC-Viptela triage."""

    def filters(self):
        """Return filter map."""
        return {
            "detect_platform_from_output": detect_platform_from_output,
            "detect_platform_from_make":    detect_platform_from_make,
            "extract_tloc_color":           extract_tloc_color,
            "is_template_managed":          is_template_managed,
            "parse_bfd_sessions":           parse_bfd_sessions,
            "parse_bfd_history":            parse_bfd_history,
            "is_bfd_not_configured":        is_bfd_not_configured,
            "is_flapping":                  is_flapping,
            "parse_control_connections":    parse_control_connections,
            "parse_interface_status":       parse_interface_status,
            "is_tloc_local":                is_tloc_local,
            "parse_omp_peers":              parse_omp_peers,
            "parse_redundant_router_ip":    parse_redundant_router_ip,
            "classify_ping_loss":           classify_ping_loss,
        }


# ---------------------------------------------------------------------------
# Platform detection
# ---------------------------------------------------------------------------

def detect_platform_from_output(output_dict):
    """Detect platform from combined show command outputs using keyword scoring.

    Args:
        output_dict: Dict of command -> raw output string.

    Returns:
        str: 'cedge', 'vedge', or ''.

    Raises:
        Exception: Re-raised after logging.
    """
    try:
        if not isinstance(output_dict, dict):
            return ""
        combined = " ".join(str(v) for v in output_dict.values()).lower()
        cedge_kw = ("uptime", "cisco ios", "ios-xe", "xe software", "c8000",
                    "isr", "asr", "16.", "17.", "sdwan system", "sdwan-enabled")
        vedge_kw = ("viptela", "vedge", "vbond", "vsmart",
                    "18.", "19.", "20.", "21.", "22.", "system status")
        c = sum(1 for kw in cedge_kw if kw in combined)
        v = sum(1 for kw in vedge_kw if kw in combined)
        if c > v:
            return "cedge"
        if v > 0:
            return "vedge"
        return ""
    except Exception as exc:
        log.error("detect_platform_from_output failed: %s", exc)
        raise


def detect_platform_from_make(make):
    """Detect platform from inventory make/manufacturer field.

    Args:
        make: Manufacturer string from ESP inventory.

    Returns:
        str: 'cedge' or 'vedge'.

    Raises:
        Exception: Re-raised after logging.
    """
    try:
        lower = str(make).lower()
        if any(kw in lower for kw in ("cisco", "ios", "csr", "asr", "isr")):
            return "cedge"
        if any(kw in lower for kw in ("viptela", "vedge")):
            return "vedge"
        return "vedge"
    except Exception as exc:
        log.error("detect_platform_from_make failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------

def extract_tloc_color(text):
    """Extract TLOC color from alarm Description text.

    Looks for common patterns like 'color: <color>' or 'TLOC <color>'.
    Falls back to known color tokens.

    Args:
        text: Full Description / Problem Summary string.

    Returns:
        str: TLOC color (lowercased), or '' if not found.

    Raises:
        Exception: Re-raised after logging.
    """
    try:
        if not text:
            return ""
        known_colors = (
            "biz-internet", "public-internet", "private1", "private2",
            "private3", "private4", "private5", "private6",
            "mpls", "metro-ethernet", "lte", "3g", "default",
            "blue", "bronze", "custom1", "custom2", "custom3",
            "gold", "green", "red", "silver",
        )
        lower = text.lower()
        match = re.search(r"color\s*[:=]\s*([a-z0-9_\-]+)", lower)
        if match:
            return match.group(1).strip()
        match = re.search(r"tloc[\s_-]+([a-z0-9_\-]+)", lower)
        if match and match.group(1) in known_colors:
            return match.group(1)
        for c in known_colors:
            if c in lower:
                return c
        return ""
    except Exception as exc:
        log.error("extract_tloc_color failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# Template detection — VALUE-based (fixes NEW-BUG-1)
# ---------------------------------------------------------------------------

def is_template_managed(output_dict):
    """Detect if vEdge/cEdge is under vManage template control.

    Checks the VALUE of vManaged: and Configuration template: fields, NOT
    keyword presence. The previous code returned True for "Configuration
    template: None" because the word "template" was present — blocking all
    CLI bounces.

    Args:
        output_dict: Dict of command -> raw output string, typically containing
                     'show system status' (vedge) or 'show sdwan system status'.

    Returns:
        bool: True only when device is confirmed template-managed.

    Raises:
        Exception: Re-raised after logging.
    """
    try:
        if not isinstance(output_dict, dict):
            return False
        system_status = ""
        for key, val in output_dict.items():
            if "system status" in key.lower():
                system_status = str(val)
                break
        not_managed_values = {"none", "n/a", "-", "false", ""}
        for line in system_status.splitlines():
            if re.match(r"\s*vmanaged\s*:", line, re.IGNORECASE):
                value = line.split(":", 1)[-1].strip().lower()
                if value == "true":
                    return True
            if re.match(r"\s*configuration template\s*:", line, re.IGNORECASE):
                value = line.split(":", 1)[-1].strip().lower()
                if value and value not in not_managed_values:
                    return True
        return False
    except Exception as exc:
        log.error("is_template_managed failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# BFD session parsing
# ---------------------------------------------------------------------------

def parse_bfd_sessions(output_dict, tloc_color=""):
    """Parse BFD session state from raw command output.

    Args:
        output_dict: Dict of command -> raw output string.
        tloc_color: Filter sessions by local-color (optional).

    Returns:
        list[dict]: [{system_ip, site_id, state, source_tloc, dest_tloc, ...}]

    Raises:
        Exception: Re-raised after logging.
    """
    try:
        sessions = []
        if not isinstance(output_dict, dict):
            return sessions
        text = ""
        for key, val in output_dict.items():
            kl = key.lower()
            if "bfd sessions" in kl and "history" not in kl:
                text += "\n" + str(val)
        if not text:
            return sessions
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            cols = stripped.split()
            if len(cols) < 6:
                continue
            if cols[0].startswith("---") or cols[0].lower() in ("system", "src"):
                continue
            sys_ip = cols[0]
            if not re.match(r"^\d+\.\d+\.\d+\.\d+$", sys_ip):
                continue
            state = ""
            color_match = ""
            for col in cols[1:]:
                low = col.lower()
                if low in ("up", "down", "init", "admin-down"):
                    state = low
                if tloc_color and low == tloc_color.lower():
                    color_match = low
            if tloc_color and not color_match:
                continue
            sessions.append({
                "system_ip": sys_ip,
                "state":     state or "unknown",
                "raw":       stripped,
            })
        return sessions
    except Exception as exc:
        log.error("parse_bfd_sessions failed: %s", exc)
        raise


def parse_bfd_history(output_dict, tloc_color=""):
    """Parse BFD history (event log) from raw output for flapping detection.

    Args:
        output_dict: Dict of command -> raw output string.
        tloc_color: Filter by TLOC color (optional).

    Returns:
        list[dict]: [{timestamp, event, raw}]

    Raises:
        Exception: Re-raised after logging.
    """
    try:
        events = []
        if not isinstance(output_dict, dict):
            return events
        text = ""
        for key, val in output_dict.items():
            if "history" in key.lower():
                text += "\n" + str(val)
        if not text:
            return events
        ts_pat = re.compile(r"^\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}")
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if tloc_color and tloc_color.lower() not in stripped.lower():
                continue
            if ts_pat.search(stripped):
                events.append({"timestamp": stripped[:19], "raw": stripped})
        return events
    except Exception as exc:
        log.error("parse_bfd_history failed: %s", exc)
        raise


def is_bfd_not_configured(output_dict):
    """Detect 'BFD not configured' from raw command output.

    Args:
        output_dict: Dict of command -> raw output string.

    Returns:
        bool: True if explicit 'not configured' / 'no bfd' signal seen.

    Raises:
        Exception: Re-raised after logging.
    """
    try:
        if not isinstance(output_dict, dict):
            return False
        combined = " ".join(str(v) for v in output_dict.values()).lower()
        markers = (
            "bfd is not configured",
            "no bfd sessions",
            "% bfd not enabled",
            "bfd protocol is not enabled",
        )
        return any(m in combined for m in markers)
    except Exception as exc:
        log.error("is_bfd_not_configured failed: %s", exc)
        raise


def is_flapping(history, window_minutes=60):
    """Determine if BFD session has flapped within given window.

    Flap = >= 3 state transitions in the time window.

    Args:
        history: Parsed BFD history list of dicts.
        window_minutes: Window size in minutes.

    Returns:
        bool: True if flapping observed.

    Raises:
        Exception: Re-raised after logging.
    """
    try:
        if not history:
            return False
        cutoff = datetime.utcnow() - timedelta(minutes=int(window_minutes))
        recent = 0
        for ev in history:
            ts_str = ev.get("timestamp", "")
            try:
                ts = datetime.strptime(ts_str[:19], "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                try:
                    ts = datetime.strptime(ts_str[:19], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue
            if ts >= cutoff:
                recent += 1
        return recent >= 3
    except Exception as exc:
        log.error("is_flapping failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# Control plane parsing
# ---------------------------------------------------------------------------

def parse_control_connections(output_dict):
    """Parse control connections from raw command output into up/down lists.

    Args:
        output_dict: Dict of command -> raw output string.

    Returns:
        dict: {"up": [<peer>, ...], "down": [<peer>, ...]}

    Raises:
        Exception: Re-raised after logging.
    """
    try:
        result = {"up": [], "down": []}
        if not isinstance(output_dict, dict):
            return result
        text = ""
        for key, val in output_dict.items():
            kl = key.lower()
            if "control connections" in kl and "history" not in kl:
                text += "\n" + str(val)
        if not text:
            return result
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            cols = stripped.split()
            if len(cols) < 4:
                continue
            if stripped.startswith("---"):
                continue
            state = ""
            peer = ""
            for col in cols:
                low = col.lower()
                if low in ("up", "down", "connect", "tear_down"):
                    state = "up" if low == "up" else "down"
                if re.match(r"^\d+\.\d+\.\d+\.\d+$", col) and not peer:
                    peer = col
            if peer and state:
                result[state].append(peer)
        return result
    except Exception as exc:
        log.error("parse_control_connections failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# Interface parsing
# ---------------------------------------------------------------------------

def parse_interface_status(output_dict, tloc_color=""):
    """Parse interface status (name + state) matching the TLOC color.

    Args:
        output_dict: Dict of command -> raw output string.
        tloc_color: TLOC color name to match against interface description.

    Returns:
        dict: {"name": <interface>, "state": <up|down|admin down|unknown>}

    Raises:
        Exception: Re-raised after logging.
    """
    try:
        result = {"name": "", "state": "unknown"}
        if not isinstance(output_dict, dict):
            return result
        text = ""
        for key, val in output_dict.items():
            if "interface" in key.lower():
                text += "\n" + str(val)
        if not text:
            return result
        color = (tloc_color or "").lower()
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if color and color in stripped.lower():
                cols = stripped.split()
                if len(cols) >= 2:
                    name = cols[0]
                    state = "unknown"
                    for col in cols[1:]:
                        low = col.lower()
                        if low in ("up", "down"):
                            state = low
                            break
                        if low.startswith("admin"):
                            state = "admin down"
                            break
                    result["name"] = name
                    result["state"] = state
                    return result
        return result
    except Exception as exc:
        log.error("parse_interface_status failed: %s", exc)
        raise


def is_tloc_local(output_dict, tloc_color=""):
    """Detect whether the TLOC terminates on this device or is via redundant router.

    Heuristic: if any 'show control local-properties' line includes the color
    AND a non-zero source IP, TLOC is local.

    Args:
        output_dict: Dict of command -> raw output.
        tloc_color: Color name.

    Returns:
        bool: True if TLOC local.

    Raises:
        Exception: Re-raised after logging.
    """
    try:
        if not isinstance(output_dict, dict):
            return False
        text = ""
        for key, val in output_dict.items():
            if "local-properties" in key.lower():
                text += "\n" + str(val)
        if not text:
            return True
        color = (tloc_color or "").lower()
        for line in text.splitlines():
            low = line.lower()
            if color and color in low:
                if re.search(r"\b\d+\.\d+\.\d+\.\d+\b", line):
                    return True
        return False
    except Exception as exc:
        log.error("is_tloc_local failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# OMP parsing — fixes BUG #7 (omp_peers was never set in scope_check)
# ---------------------------------------------------------------------------

def parse_omp_peers(omp_raw_output):
    """Parse OMP peer table into up/down lists.

    Args:
        omp_raw_output: Dict of command -> raw output (or raw string).

    Returns:
        dict: {"up": [<peer_ip>, ...], "down": [<peer_ip>, ...]}

    Raises:
        Exception: Re-raised after logging.
    """
    try:
        result = {"up": [], "down": []}
        if not omp_raw_output:
            return result
        if isinstance(omp_raw_output, dict):
            text = ""
            for key, val in omp_raw_output.items():
                if "omp peers" in key.lower():
                    text = str(val)
                    break
            if not text:
                text = "\n".join(str(v) for v in omp_raw_output.values())
        else:
            text = str(omp_raw_output)
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("---") or stripped.lower().startswith("peer"):
                continue
            cols = stripped.split()
            if len(cols) < 6:
                continue
            peer_ip = cols[0]
            if not re.match(r"^\d+\.\d+\.\d+\.\d+$", peer_ip):
                continue
            state = ""
            for col in cols[1:]:
                low = col.lower()
                if low in ("up", "down"):
                    state = low
                    break
            if state == "up":
                result["up"].append(peer_ip)
            elif state == "down":
                result["down"].append(peer_ip)
        return result
    except Exception as exc:
        log.error("parse_omp_peers failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# Redundant router
# ---------------------------------------------------------------------------

def parse_redundant_router_ip(output_dict, device_ip):
    """Extract redundant router IP from VRRP output, excluding device_ip.

    Args:
        output_dict: Dict of command -> raw output (VRRP).
        device_ip: This device's MgmtIP — must be excluded from result.

    Returns:
        str: Redundant router IP, or '' if not found.

    Raises:
        Exception: Re-raised after logging.
    """
    try:
        if not isinstance(output_dict, dict):
            return ""
        text = ""
        for key, val in output_dict.items():
            if "vrrp" in key.lower():
                text += "\n" + str(val)
        if not text:
            return ""
        for line in text.splitlines():
            for token in line.split():
                if re.match(r"^\d+\.\d+\.\d+\.\d+$", token) and token != device_ip:
                    return token
        return ""
    except Exception as exc:
        log.error("parse_redundant_router_ip failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# Ping classification
# ---------------------------------------------------------------------------

def classify_ping_loss(loss_pct):
    """Classify packet loss percentage into MOP-aligned tiers.

    Tiers:
      HEALTHY     : 0%
      MINOR       : 1-10%
      DEGRADED    : 11-30%
      SEVERE      : 31-99%
      UNREACHABLE : 100%

    Args:
        loss_pct: Packet loss percentage (int or string).

    Returns:
        str: One of HEALTHY / MINOR / DEGRADED / SEVERE / UNREACHABLE.

    Raises:
        Exception: Re-raised after logging.
    """
    try:
        pct = int(str(loss_pct).strip().rstrip("%"))
        if pct <= 0:
            return "HEALTHY"
        if 1 <= pct <= 10:
            return "MINOR"
        if 11 <= pct <= 30:
            return "DEGRADED"
        if 31 <= pct <= 99:
            return "SEVERE"
        return "UNREACHABLE"
    except Exception as exc:
        log.error("classify_ping_loss failed: %s", exc)
        raise
