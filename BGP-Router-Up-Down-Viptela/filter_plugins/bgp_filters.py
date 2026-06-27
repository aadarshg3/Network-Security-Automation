"""Filter plugins for BGP-Router-Up-Down-Viptela playbook."""
import re
import logging

log = logging.getLogger(__name__)


class FilterModule:
    """Ansible filter plugin for BGP Router Up Down Viptela triage."""

    def filters(self):
        """Return filter map."""
        return {
            "detect_platform_from_output": detect_platform_from_output,
            "detect_platform_from_make": detect_platform_from_make,
            "extract_vpn_from_text": extract_vpn_from_text,
            "extract_peer_sysip_from_text": extract_peer_sysip_from_text,
            "parse_bgp_state_cedge": parse_bgp_state_cedge,
            "parse_bgp_state_vedge": parse_bgp_state_vedge,
            "get_stuck_neighbors": get_stuck_neighbors,
            "is_template_managed": is_template_managed,
            "parse_interface_list_cedge": parse_interface_list_cedge,
            "parse_interface_list_vedge": parse_interface_list_vedge,
            "select_lan_down_interfaces": select_lan_down_interfaces,
            "build_clear_commands_cedge": build_clear_commands_cedge,
            "build_clear_commands_vedge": build_clear_commands_vedge,
            "get_bgp_state_diagnosis": get_bgp_state_diagnosis,
            "get_wan_interface_vedge": get_wan_interface_vedge,
            "get_wan_interface_cedge": get_wan_interface_cedge,
        }


# ---------------------------------------------------------------------------
# Platform detection
# ---------------------------------------------------------------------------

def detect_platform_from_output(output_dict: dict) -> str:
    """Detect platform from combined show command outputs using keyword scoring.

    Args:
        output_dict: Dict of command -> raw output string.

    Returns:
        str: 'cedge', 'vedge', or ''.

    Raises:
        Exception: On unexpected input.
    """
    try:
        combined = " ".join(str(v) for v in output_dict.values()).lower()
        cedge_kw = ("uptime", "cisco ios", "ios-xe", "xe software", "c8000",
                    "isr", "asr", "16.", "17.", "sdwan system", "sdwan-enabled")
        vedge_kw = ("viptela", "vedge", "vbond", "vsmart",
                    "18.", "19.", "20.", "21.", "22.", "system status")
        cedge_score = sum(1 for kw in cedge_kw if kw in combined)
        vedge_score = sum(1 for kw in vedge_kw if kw in combined)
        if cedge_score > vedge_score:
            return "cedge"
        if vedge_score > 0:
            return "vedge"
        return ""
    except Exception as exc:
        log.error("detect_platform_from_output failed: %s", exc)
        raise


def detect_platform_from_make(make: str) -> str:
    """Detect platform from inventory make/manufacturer field.

    Args:
        make: Manufacturer string from ESP inventory.

    Returns:
        str: 'cedge' or 'vedge'.

    Raises:
        Exception: On failure.
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

def extract_vpn_from_text(alarm_text: str) -> str:
    """Extract VPN/VRF ID from alarm TEXT field.

    The TEXT format is: 'All BGP peering sessions are down- <hostname> <ip> <ip> <vpn>'
    The trailing integer is the VPN ID.

    Args:
        alarm_text: Full alarm TEXT string.

    Returns:
        str: VPN ID as string, defaults to '0'.

    Raises:
        Exception: On parse failure.
    """
    try:
        tokens = alarm_text.strip().split()
        if tokens:
            last = tokens[-1]
            if re.match(r"^\d+$", last):
                return last
        return "0"
    except Exception as exc:
        log.error("extract_vpn_from_text failed: %s", exc)
        raise


def extract_peer_sysip_from_text(alarm_text: str) -> str:
    """Extract BGP peer system-IP from alarm TEXT field.

    TEXT format confirmed from MOP image2:
      'All BGP peering sessions are down- {hostname}  {mgmt_ip}  {peer_ip}  {vpn}'

    The SECOND IP is the BGP peer system-IP.
    The FIRST IP is the management IP of the alerting device (same as MgmtIP).

    In the SIT test both IPs happen to be identical (192.168.31.21), so
    returning ips[0] was not caught. In production they are always different.

    Args:
        alarm_text: Full alarm TEXT string.

    Returns:
        str: Peer system-IP (second IP in TEXT) or first IP as fallback.

    Raises:
        Exception: On parse failure.
    """
    try:
        ip_pattern = re.compile(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b")
        ips = ip_pattern.findall(alarm_text)
        if len(ips) >= 2:
            return ips[1]   # second IP = BGP peer system-IP
        return ips[0] if ips else ""
    except Exception as exc:
        log.error("extract_peer_sysip_from_text failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# BGP state parsing
# ---------------------------------------------------------------------------

def parse_bgp_state_cedge(output_text: str) -> list:
    """Parse BGP neighbor states from cEdge 'show ip bgp ... neighbors | include BGP' output.

    Parses lines of the form:
      BGP neighbor is 172.28.240.96, vrf 10, remote AS 65534, external link
      BGP state = Established, up for 2d09h
      BGP version 4, ...

    Args:
        output_text: Raw command output string.

    Returns:
        list: List of dicts {neighbor, state, remote_as, vrf}.

    Raises:
        Exception: On parse failure.
    """
    neighbors = []
    try:
        current = {}
        for line in str(output_text).splitlines():
            line = line.strip()
            # Neighbor header line
            nbr_match = re.search(
                r"BGP neighbor is\s+(\S+?)(?:,\s*vrf\s+(\S+?))?(?:,\s*remote AS\s+(\d+))?",
                line, re.IGNORECASE
            )
            if nbr_match:
                if current.get("neighbor"):
                    neighbors.append(current)
                current = {
                    "neighbor": nbr_match.group(1).rstrip(","),
                    "vrf": (nbr_match.group(2) or "default").rstrip(","),
                    "remote_as": nbr_match.group(3) or "",
                    "state": "unknown",
                }
                continue
            # State line
            state_match = re.search(r"BGP state\s*=\s*(\w+)", line, re.IGNORECASE)
            if state_match and current:
                current["state"] = state_match.group(1).lower()
                continue
            # Remote AS line (fallback)
            as_match = re.search(r"remote AS\s+(\d+)", line, re.IGNORECASE)
            if as_match and current and not current.get("remote_as"):
                current["remote_as"] = as_match.group(1)
        if current.get("neighbor"):
            neighbors.append(current)
        return neighbors
    except Exception as exc:
        log.error("parse_bgp_state_cedge failed: %s", exc)
        raise


def parse_bgp_state_vedge(output_text: str, vpn_id: str = "0") -> list:
    """Parse BGP neighbor states from vEdge 'show bgp summary' output.

    Handles multi-VPN output — vEdge 'show bgp summary' prints one section
    per VPN. Each section starts with 'vpn <id>' and contains a neighbor table.

    Confirmed vEdge column order (20.x OS):
      NEIGHBOR  AS  MSG_RCVD  MSG_SENT  OUT_Q  UPTIME  PREFIX_RCVD  PREFIX_VALID  PREFIX_INSTALLED  STATE

    UPTIME may be empty (blank) when session has never established — the regex
    must not require it.  STATE is always the last token on the data row.

    Args:
        output_text: Raw show bgp summary output (may contain multiple VPN blocks).
        vpn_id: VPN ID from ticket — used to tag results and to filter when
                specific VPN is requested ('0' means accept all).

    Returns:
        list: List of dicts {neighbor, state, remote_as, vrf}.

    Raises:
        Exception: On parse failure.
    """
    neighbors = []
    try:
        current_vpn = "0"
        in_table = False

        for line in str(output_text).splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            # Detect VPN section header — reset table state for each VPN block
            vpn_match = re.match(r"^vpn\s+(\d+)\s*$", stripped, re.IGNORECASE)
            if vpn_match:
                current_vpn = vpn_match.group(1)
                in_table = False
                continue

            # Detect column header row — marks start of neighbor table
            if re.search(r"NEIGHBOR\s+.*STATE", stripped, re.IGNORECASE):
                in_table = True
                continue

            if not in_table:
                continue

            # Skip separator lines
            if re.match(r"^-+$", stripped):
                continue

            # Data row — first token must be an IPv4 address
            parts = stripped.split()
            if not parts:
                continue
            if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", parts[0]):
                continue

            # STATE is always the last token; remote AS is always second token
            state = parts[-1].lower()
            remote_as = parts[1] if len(parts) > 1 else ""

            # Filter: only return neighbors for requested VPN (or all if vpn_id == '0')
            if str(vpn_id) not in ("0", "") and current_vpn != str(vpn_id):
                continue

            neighbors.append({
                "neighbor": parts[0],
                "remote_as": remote_as,
                "vrf": current_vpn,
                "state": state,
            })

        return neighbors
    except Exception as exc:
        log.error("parse_bgp_state_vedge failed: %s", exc)
        raise


def get_stuck_neighbors(neighbors: list) -> list:
    """Filter neighbors in non-Established (stuck) states.

    Stuck states: idle, active, connect, opensent, openconfirm.
    Never includes Established — those are healthy.

    Args:
        neighbors: List of neighbor dicts from parse_bgp_state_*.

    Returns:
        list: Subset of neighbors in stuck states.

    Raises:
        Exception: On failure.
    """
    stuck_states = {"idle", "active", "connect", "opensent", "openconfirm"}
    try:
        return [n for n in neighbors if n.get("state", "").lower() in stuck_states]
    except Exception as exc:
        log.error("get_stuck_neighbors failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# Template managed detection
# ---------------------------------------------------------------------------

def is_template_managed(output_dict: dict) -> bool:
    """Detect if vEdge device is managed by a vManage configuration template.

    Two authoritative fields from 'show system status':
      1. vManaged: true/false  — device is under vManage control
      2. Configuration template: <name>/None — active template attached

    Both fields must be checked by VALUE, not by keyword presence.
    'Configuration template: None' means NO template → returns False.

    Args:
        output_dict: Dict of command -> raw output string.

    Returns:
        bool: True only when device is confirmed template-managed.

    Raises:
        Exception: On failure.
    """
    try:
        system_status = ""
        for key, val in output_dict.items():
            if "system status" in key.lower():
                system_status = str(val)
                break

        not_managed_values = {"none", "n/a", "-", "false", ""}

        for line in system_status.splitlines():
            # Check vManaged field — authoritative primary indicator
            if re.match(r"\s*vmanaged\s*:", line, re.IGNORECASE):
                value = line.split(":", 1)[-1].strip().lower()
                if value == "true":
                    return True

            # Check Configuration template field — value must be a real name
            if re.match(r"\s*configuration template\s*:", line, re.IGNORECASE):
                value = line.split(":", 1)[-1].strip().lower()
                if value and value not in not_managed_values:
                    return True

        return False
    except Exception as exc:
        log.error("is_template_managed failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# Interface parsing and LAN selection
# ---------------------------------------------------------------------------

def parse_interface_list_cedge(output_text: str) -> list:
    """Parse cEdge 'show int description' output into interface list.

    Columns: Interface  Status  Protocol  Description
    Example:
      Gi0/0/0    up    up    WAN_MPLS
      Gi0/0/1    down  down  LAN_CUSTOMER

    Args:
        output_text: Raw show int description output.

    Returns:
        list: List of dicts {name, status, protocol, description}.

    Raises:
        Exception: On parse failure.
    """
    interfaces = []
    try:
        for line in str(output_text).splitlines():
            line = line.strip()
            if not line or re.match(r"^Interface", line, re.IGNORECASE):
                continue
            parts = line.split()
            if len(parts) >= 3:
                description = " ".join(parts[3:]) if len(parts) > 3 else ""
                interfaces.append({
                    "name": parts[0],
                    "status": parts[1].lower(),
                    "protocol": parts[2].lower(),
                    "description": description,
                })
        return interfaces
    except Exception as exc:
        log.error("parse_interface_list_cedge failed: %s", exc)
        raise


def parse_interface_list_vedge(output_text: str) -> list:
    """Parse vEdge 'show interface description' output into interface list.

    vEdge column order (from live device verified):
      VPN(0) INTERFACE(1) TYPE(2) IP(3) ADMIN_STATUS(4) OPER_STATUS(5) TRACKER(6) DESC(7+)

    Also parses VPN ID so LAN/WAN classification can use structural
    attributes (vpn != 0 = service/LAN) instead of description only.

    Args:
        output_text: Raw show interface description output.

    Returns:
        list: List of dicts {name, vpn, admin_status, oper_status, description}.

    Raises:
        Exception: On parse failure.
    """
    interfaces = []
    try:
        for line in str(output_text).splitlines():
            line = line.strip()
            if not line:
                continue
            # Skip header lines
            if re.match(r"^(VPN|Interface|-)", line, re.IGNORECASE):
                continue
            parts = line.split()
            if len(parts) < 6:
                continue
            vpn = parts[0].strip()
            name = parts[1].strip()
            admin_status = parts[4].lower().strip()
            oper_status = parts[5].lower().strip()
            description = " ".join(parts[7:]).strip() if len(parts) > 7 else ""
            interfaces.append({
                "name": name,
                "vpn": vpn,
                "status": admin_status,
                "protocol": oper_status,
                "description": description,
            })
        return interfaces
    except Exception as exc:
        log.error("parse_interface_list_vedge failed: %s", exc)
        raise


def select_lan_down_interfaces(interfaces: list) -> list:
    """Select interfaces that are LAN-side and operationally down.

    LAN classification uses VPN column as primary signal (structural,
    consistent regardless of naming convention):
      - VPN != 0 → service/LAN side (vEdge)
      - VPN == 0 → transport/WAN side — excluded
    Description containing 'lan' is kept as secondary signal for cEdge
    where VPN column is not available.

    Down condition: admin-Up AND oper-Down.
    This is the real failure case — not intentionally shut (admin-Down),
    but link has actually gone down (oper-Down).

    Guards:
    - Never select tunnel, loopback, management, or virtual interfaces.
    - Never select VPN 0 (transport/WAN) interfaces.

    Args:
        interfaces: List of interface dicts from parse_interface_list_*.

    Returns:
        list: Interface name strings safe to bounce.

    Raises:
        Exception: On failure.
    """
    safe = []
    excluded_prefixes = ("tu", "loop", "lo", "null", "vl", "bdi", "mg", "bvi")
    try:
        for iface in interfaces:
            name = iface.get("name", "").lower()
            description = iface.get("description", "").lower()
            status = iface.get("status", "").lower()
            protocol = iface.get("protocol", "").lower()
            vpn = str(iface.get("vpn", "")).strip()

            # Exclude tunnel/loopback/management/virtual
            if any(name.startswith(pfx) for pfx in excluded_prefixes):
                continue

            # LAN classification:
            # Primary: VPN != 0 (vEdge structural — VPN 0 is always WAN/transport)
            # Secondary: description contains 'lan' (cEdge fallback)
            is_lan_by_vpn = vpn != "" and vpn != "0"
            is_lan_by_desc = "lan" in description
            if not (is_lan_by_vpn or is_lan_by_desc):
                continue

            # Target: admin-Up but oper-Down (link failure, not intentional shutdown)
            if status != "up" or protocol != "down":
                continue

            safe.append(iface.get("name", ""))

        return safe
    except Exception as exc:
        log.error("select_lan_down_interfaces failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# BGP clear command builders
# ---------------------------------------------------------------------------

def build_clear_commands_cedge(stuck_neighbors: list, vpn_id: str = "0") -> list:
    """Build cEdge BGP clear commands for stuck neighbors.

    Uses: clear ip bgp vpnv4 vrf <vpn> <neighbor-ip>
    For default VRF (vpn 0): clear ip bgp <neighbor-ip>

    Args:
        stuck_neighbors: List of neighbor dicts with 'neighbor' key.
        vpn_id: VPN/VRF ID string.

    Returns:
        list: List of clear command strings.

    Raises:
        Exception: On failure.
    """
    try:
        commands = []
        for nbr in stuck_neighbors:
            ip = nbr.get("neighbor", "")
            if not ip:
                continue
            if str(vpn_id) in ("0", ""):
                commands.append(f"clear ip bgp {ip}")
            else:
                commands.append(f"clear ip bgp vpnv4 vrf {vpn_id} {ip}")
        return commands
    except Exception as exc:
        log.error("build_clear_commands_cedge failed: %s", exc)
        raise


def build_clear_commands_vedge(stuck_neighbors: list, vpn_id: str = "0") -> list:
    """Build vEdge BGP clear commands for stuck neighbors.

    Confirmed vEdge OS syntax: clear bgp neighbor <ip> vpn <vpn_id>
    VPN qualifier is MANDATORY — device prompts for it if omitted.
    Confirmed on live vEdge 20.3.1: clear bgp neighbor 1.1.1.1 vpn 0 → works.

    Args:
        stuck_neighbors: List of neighbor dicts with 'neighbor' key.
        vpn_id: VPN ID string (informational only — not used in command).

    Returns:
        list: List of clear command strings.

    Raises:
        Exception: On failure.
    """
    try:
        commands = []
        for nbr in stuck_neighbors:
            ip = nbr.get("neighbor", "")
            if not ip:
                continue
            commands.append(f"clear bgp neighbor {ip} vpn {vpn_id}")
        return commands
    except Exception as exc:
        log.error("build_clear_commands_vedge failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# GAP 5 — BGP state diagnostic reasoning
# v10: per-state explanation of what each stuck state means
# ---------------------------------------------------------------------------

def get_bgp_state_diagnosis(state: str) -> str:
    """Return diagnostic reasoning for a stuck BGP session state.

    Maps each stuck BGP state to its most likely cause per MOP guidance.

    Args:
        state: BGP session state string (case-insensitive).

    Returns:
        str: Human-readable diagnosis string for NOC.

    Raises:
        Exception: On failure.
    """
    try:
        state_lower = str(state).strip().lower()
        diagnoses = {
            "idle": (
                "BGP session in IDLE state. Most likely causes:\n"
                "  a. Neighbor IP address mismatch (configured IP differs from actual peer IP)\n"
                "  b. Wrong AS number configured for this neighbor\n"
                "  c. Neighbor not configured on the ISP/peer side\n"
                "  d. BGP process restarted or neighbor was administratively cleared\n"
                "  Action: Verify neighbor IP and remote-AS on both sides. "
                "Check 'show running-config | section bgp' (cEdge) or "
                "'show running-config vpn X router bgp' (vEdge)."
            ),
            "active": (
                "BGP session in ACTIVE state. Most likely causes:\n"
                "  a. TCP port 179 blocked by ACL, Firewall, or ISP\n"
                "  b. Route to BGP peer exists but TCP connection is refused\n"
                "  c. BGP MD5 authentication mismatch\n"
                "  d. Wrong update-source interface configured\n"
                "  Action: Verify TCP port 179 is permitted in ACLs on both sides. "
                "Check if ISP is filtering BGP. Verify MD5 password if configured. "
                "Run 'show ip routes vpn {vpn_id}' (vEdge) or 'show ip route <peer>' (cEdge) to confirm routing."
            ),
            "connect": (
                "BGP session in CONNECT state. Most likely causes:\n"
                "  a. TCP three-way handshake not completing\n"
                "  b. Asymmetric routing — SYN reaches peer but SYN-ACK returns "
                "via different path that may be filtered\n"
                "  c. MTU mismatch causing TCP fragmentation issues\n"
                "  Action: Check for asymmetric routing. Verify MTU on the path. "
                "Run traceroute to peer to verify forward and return path."
            ),
            "opensent": (
                "BGP session in OPENSENT state. Most likely causes:\n"
                "  a. AS number mismatch — local AS does not match peer's expectation\n"
                "  b. BGP authentication (MD5) mismatch\n"
                "  c. BGP OPEN message rejected by peer\n"
                "  Action: Verify remote-AS configuration matches peer's local-AS. "
                "Check 'show running-config | section bgp' (cEdge) or 'show running-config vpn X router bgp' (vEdge) for AS and auth config. "
                "Check BGP logs for NOTIFICATION messages."
            ),
            "openconfirm": (
                "BGP session in OPENCONFIRM state. Most likely causes:\n"
                "  a. AS number mismatch in OPEN message exchange\n"
                "  b. BGP authentication (MD5) key mismatch\n"
                "  c. Capability mismatch (address families)\n"
                "  Action: Same as OPENSENT — verify AS and authentication. "
                "Check BGP neighbor log for the specific NOTIFICATION error code."
            ),
            "unknown": (
                "BGP session in UNKNOWN state. State could not be determined. "
                "Check 'show bgp summary' directly on the device."
            ),
        }
        return diagnoses.get(state_lower, (
            f"BGP session in {state.upper()} state. "
            "Check 'show bgp summary' and 'show bgp neighbor' for details."
        ))
    except Exception as exc:
        log.error("get_bgp_state_diagnosis failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# WAN interface extraction — for VPN-sourced ping
# MOP image2: "Ping <neighbor-ip> vpn 0 source <wan-interface>"
# ---------------------------------------------------------------------------

def get_wan_interface_vedge(output_text: str) -> str:
    """Extract first UP transport (WAN) interface from vEdge 'show interface' output.

    vEdge 'show interface' columns include PORT TYPE field.
    Transport interfaces (WAN) have PORT TYPE = 'transport'.
    We pick the first one that is Admin UP and Oper UP.

    Args:
        output_text: Raw 'show interface' output string.

    Returns:
        str: Interface name (e.g. 'ge0/0') or '' if not found.

    Raises:
        Exception: On parse failure.
    """
    try:
        for line in str(output_text).splitlines():
            parts = line.split()
            if len(parts) < 7:
                continue
            # Column layout from show interface (vEdge):
            # VPN  INTERFACE  AF  IP  IF-STATUS  IF-OPER  TRACKER  ENCAP  PORT-TYPE ...
            # We look for: vpn=0, port_type=transport, admin=Up, oper=Up
            # Port type is at index 8 in the standard output
            try:
                vpn_col = parts[0]
                iface_col = parts[1]
                admin_status = parts[4].lower() if len(parts) > 4 else ""
                oper_status = parts[5].lower() if len(parts) > 5 else ""
                port_type = parts[8].lower() if len(parts) > 8 else ""
            except IndexError:
                continue

            if (vpn_col == "0"
                    and port_type == "transport"
                    and admin_status == "up"
                    and oper_status == "up"):
                return iface_col

        return ""
    except Exception as exc:
        log.error("get_wan_interface_vedge failed: %s", exc)
        return ""


def get_wan_interface_cedge(output_text: str) -> str:
    """Extract first UP WAN interface from cEdge 'show ip int brief' output.

    For cEdge SD-WAN, WAN interfaces typically start with Gi0/0/0, Gi0/1,
    Tu (tunnel), or are the first non-management UP/UP interface.
    We return the first non-loopback, non-management UP/UP interface.

    Args:
        output_text: Raw 'show ip int brief' output string.

    Returns:
        str: Interface name (e.g. 'GigabitEthernet0/0/0') or '' if not found.

    Raises:
        Exception: On parse failure.
    """
    try:
        excluded = ("loop", "lo", "null", "mgmt", "mg", "vlan", "bdi")
        for line in str(output_text).splitlines():
            parts = line.split()
            if len(parts) < 6:
                continue
            iface = parts[0]
            iface_lower = iface.lower()
            status = parts[4].lower() if len(parts) > 4 else ""
            protocol = parts[5].lower() if len(parts) > 5 else ""

            if any(iface_lower.startswith(ex) for ex in excluded):
                continue
            if status == "up" and protocol == "up":
                return iface

        return ""
    except Exception as exc:
        log.error("get_wan_interface_cedge failed: %s", exc)
        return ""
