#!/usr/bin/env python3
"""
Ansible filter plugin for Cisco-Router-Device-Down role.
v5: LIST returns from parse functions, pre-computed facts,
    VBSM sanitizer (update→notify, execute→run),
    diff_running_configs, wan signal reasons.
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re
import json
import difflib
import ipaddress
import logging
from collections import Counter

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Interface abbreviation helpers
# ---------------------------------------------------------------------------

_IFACE_PREFIXES = [
    ('GigabitEthernet', 'Gi'), ('FastEthernet', 'Fa'),
    ('TenGigabitEthernet', 'Te'), ('HundredGigE', 'Hu'),
    ('FortyGigabitEthernet', 'Fo'), ('TwentyFiveGigE', 'Twe'),
    ('Serial', 'Se'), ('Loopback', 'Lo'), ('Tunnel', 'Tu'),
    ('Vlan', 'Vl'), ('BDI', 'BDI'), ('Bundle-Ether', 'BE'),
    ('Management', 'Mg'), ('Port-channel', 'Po'),
]

def _expand_iface(name):
    """Expand abbreviated interface name to full form."""
    n = name.strip()
    for full, abbr in _IFACE_PREFIXES:
        if n.lower().startswith(abbr.lower()):
            return full + n[len(abbr):]
    return n

def _abbrev_iface(name):
    """Abbreviate interface name."""
    n = name.strip()
    for full, abbr in _IFACE_PREFIXES:
        if n.lower().startswith(full.lower()):
            return abbr + n[len(full):]
    return n

def _iface_match(a, b):
    """Return True if two interface names refer to the same interface."""
    return (_expand_iface(a).lower() == _expand_iface(b).lower() or
            _abbrev_iface(a).lower() == _abbrev_iface(b).lower() or
            a.lower() == b.lower())

# ---------------------------------------------------------------------------
# 1. safe_json_parse
# ---------------------------------------------------------------------------

def safe_json_parse(value):
    """Safely parse JSON returned by device_ssh.py / ping.py.

    Guarantees the return is always a dict containing an 'outputs' dict and a
    'packet_loss' int, so downstream '.outputs.get(...)' and '.packet_loss'
    access can never raise on a skipped task, empty stdout, or malformed JSON.
    """
    def _normalize(d):
        if not isinstance(d, dict):
            d = {'success': False, 'error': 'non-object JSON', 'output': ''}
        if 'outputs' not in d or not isinstance(d.get('outputs'), dict):
            d['outputs'] = d.get('outputs') if isinstance(d.get('outputs'), dict) else {}
        if 'packet_loss' not in d:
            d['packet_loss'] = 100
        return d

    if isinstance(value, dict):
        return _normalize(dict(value))
    try:
        return _normalize(json.loads(value))
    except Exception as exc:
        preview = str(value)[:300] if value else 'empty'
        return {
            'success': False,
            'error': f'JSON parse failed: {exc} | preview: {preview}',
            'output': '',
            'outputs': {},
            'packet_loss': 100,
        }

# ---------------------------------------------------------------------------
# 2. extract_platform
# ---------------------------------------------------------------------------

def extract_platform(show_version_text):
    """
    Detect platform from show version output.
    Returns 'ios', 'ios_xe', or 'ios_xr'.
    """
    if not show_version_text:
        return 'ios'
    t = show_version_text.lower()

    if 'ios xr' in t or 'iosxr' in t or 'cisco xr' in t:
        return 'ios_xr'
    if ('ios-xe' in t or 'ios xe' in t or 'ios_xe' in t
            or 'universal' in t or 'denali' in t or 'fuji' in t
            or 'everest' in t or 'asr1' in t):
        return 'ios_xe'
    # vios_l2 is Layer-2 IOSv (switch image) — still classify as ios
    return 'ios'

# ---------------------------------------------------------------------------
# 3. parse_interface_state  (v4 fix: returns LIST not tuple)
# ---------------------------------------------------------------------------

def parse_interface_state(show_ip_int_brief, interface_name):
    """
    Return ['line_status', 'protocol'] LIST for the given interface.
    v4 fix: list return (tuple was serialized to string by Ansible, breaking [0] access).
    """
    if not show_ip_int_brief or not interface_name:
        return ['unknown', 'unknown']

    for line in show_ip_int_brief.splitlines():
        parts = line.split()
        if len(parts) < 4 or parts[0].lower() == 'interface':
            continue

        if not _iface_match(interface_name, parts[0]):
            continue

        protocol = parts[-1]

        if 'administratively' in line.lower():
            return ['administratively down', protocol]

        status = parts[-2]
        return [status, protocol]

    return ['unknown', 'unknown']

# ---------------------------------------------------------------------------
# 4. parse_interface_ip_mask  (v4 fix: returns LIST not tuple)
# ---------------------------------------------------------------------------

def parse_interface_ip_mask(show_running, interface_name):
    """
    Return ['ip_address', 'subnet_mask'] LIST from running-config.
    v4 fix: list return.
    """
    if not show_running or not interface_name:
        return ['', '']

    in_block = False
    iface_pattern = re.compile(
        r'^interface\s+' + re.escape(_expand_iface(interface_name)),
        re.IGNORECASE
    )
    iface_pattern_abbr = re.compile(
        r'^interface\s+' + re.escape(_abbrev_iface(interface_name)),
        re.IGNORECASE
    )

    for line in show_running.splitlines():
        stripped = line.strip()

        if iface_pattern.match(stripped) or iface_pattern_abbr.match(stripped):
            in_block = True
            continue

        if in_block:
            if re.match(r'^interface\s+', stripped) or stripped == '!':
                break
            m = re.search(
                r'ip address\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)',
                stripped
            )
            if m:
                return [m.group(1), m.group(2)]

    return ['', '']

# ---------------------------------------------------------------------------
# 5. parse_default_route_interface
# ---------------------------------------------------------------------------

def parse_default_route_interface(show_ip_route):
    """
    Extract exit interface from static default route (0.0.0.0/0).
    Returns empty string if route is next-hop-only.
    """
    if not show_ip_route:
        return ''
    for line in show_ip_route.splitlines():
        if '0.0.0.0' in line and re.search(r'S[*\s]', line):
            # via X.X.X.X, GigabitEthernetY/Z
            m = re.search(r'via\s+\d+\.\d+\.\d+\.\d+,\s*(\S+)', line)
            if m:
                return m.group(1)
            # directly connected via interface
            m = re.search(
                r'(?:Gi|Fa|Se|Te|Hu|Lo|Tu|Vl|Po|Be|BDI)\S+',
                line
            )
            if m and 'via' not in line:
                return m.group(0)
    return ''

# ---------------------------------------------------------------------------
# 6. parse_static_default_next_hop
# ---------------------------------------------------------------------------

def parse_static_default_next_hop(show_ip_route):
    """Extract next-hop IP from static default route."""
    if not show_ip_route:
        return ''
    for line in show_ip_route.splitlines():
        if '0.0.0.0' in line and re.search(r'S[*\s]', line):
            m = re.search(r'via\s+(\d+\.\d+\.\d+\.\d+)', line)
            if m:
                return m.group(1)
    return ''

# ---------------------------------------------------------------------------
# 7. WAN interface helpers
# ---------------------------------------------------------------------------

_WAN_DESC_KEYWORDS = re.compile(
    r'\b(wan|mpls|inet|internet|uplink|isp|transit|provider|pe|core|bb|backbone|'
    r'access|circuit|broadband|dsl|fiber|fibre|lte|4g|5g|sdwan)\b',
    re.IGNORECASE
)

def _find_wan_by_description(show_int_desc):
    """Scan 'show interfaces description' for WAN keywords."""
    if not show_int_desc:
        return ''
    for line in show_int_desc.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        iface = parts[0]
        # Skip loopback, vlan, port-channel (management/layer2)
        if re.match(r'^(Lo|Vl|Po|BDI)', iface, re.IGNORECASE):
            continue
        # Status must be up/up (or at least up line protocol)
        if len(parts) >= 3 and parts[1].lower() not in ('up', 'down'):
            continue
        description_part = ' '.join(parts[3:]) if len(parts) > 3 else ''
        if _WAN_DESC_KEYWORDS.search(description_part):
            return iface
    return ''

def _find_bgp_wan_interface(bgp_summary_text, show_running):
    """
    Find WAN interface by BGP neighbor on /30 or /31 subnet.
    Identifies interfaces whose IP is on the same /30 or /31 as a BGP neighbor.
    """
    if not bgp_summary_text or not show_running:
        return ''

    # Extract BGP neighbors from summary
    bgp_neighbors = []
    for line in bgp_summary_text.splitlines():
        m = re.match(r'^\s*(\d+\.\d+\.\d+\.\d+)\s+\d+\s+\d+', line)
        if m:
            bgp_neighbors.append(m.group(1))

    if not bgp_neighbors:
        return ''

    # Find all interface IPs from running config
    iface_ips = {}
    current_iface = None
    for line in show_running.splitlines():
        stripped = line.strip()
        m = re.match(r'^interface\s+(\S+)', stripped, re.IGNORECASE)
        if m:
            current_iface = m.group(1)
            continue
        if current_iface:
            m = re.search(
                r'ip address\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)',
                stripped
            )
            if m:
                iface_ips[current_iface] = (m.group(1), m.group(2))

    # Check if any BGP neighbor is on same /30 or /31 as an interface
    for iface, (ip, mask) in iface_ips.items():
        # Skip loopback
        if re.match(r'^Lo', iface, re.IGNORECASE):
            continue
        try:
            iface_net = ipaddress.IPv4Network(f'{ip}/{mask}', strict=False)
            prefix_len = iface_net.prefixlen
            if prefix_len not in (30, 31):
                continue
            for neighbor in bgp_neighbors:
                if ipaddress.IPv4Address(neighbor) in iface_net:
                    return iface
        except Exception:
            continue

    return ''

# v11: Circuit-ID pattern. NOC confirmed WAN descriptions almost always carry a
# circuit ID shaped as 'c' followed by exactly 7 digits (e.g. c3026553 inside
# "199902687:MICHELIN:c3026553"). Prefix text varies; the c+7digits token does not.
_CIRCUIT_ID = re.compile(r'\bc\d{7}\b', re.IGNORECASE)


def _find_wan_by_circuit_id(show_int_desc):
    """Scan 'show interfaces description' for a circuit-ID token (c + 7 digits).
    Strong WAN signal — circuit IDs appear on provider-facing interfaces only.
    Loopback/VLAN/Port-channel skipped."""
    if not show_int_desc:
        return ''
    for line in show_int_desc.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        iface = parts[0]
        if re.match(r'^(Lo|Vl|Po|BDI|Tu|Nu)', iface, re.IGNORECASE):
            continue
        description_part = ' '.join(parts[3:])
        if _CIRCUIT_ID.search(description_part):
            return iface
    return ''


def _find_first_l3_interface(show_ip_int_brief):
    """v11 tie-breaker: NOC says the WAN is the first physical interface in
    70-80% of sites. LOW-weight signal — used only to break ties / nudge PE
    derivation, never to authorise a bounce on its own.
    Returns the first physical L3 interface that has an assigned IP, skipping
    loopback/vlan/port-channel/tunnel/null."""
    if not show_ip_int_brief:
        return ''
    for line in show_ip_int_brief.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        iface = parts[0]
        if not re.match(r'^(Gi|Te|Fa|Et|Hu|Fo|Twe|Two|Se)', iface, re.IGNORECASE):
            continue
        ip = parts[1]
        if re.match(r'^\d+\.\d+\.\d+\.\d+$', ip):   # has an assigned IP
            return iface
    return ''


def corroborate_wan_pe_from_static(show_ip_route, show_running):
    """
    v11: Static-case corroboration. Match the static default next-hop to the
    connected route whose subnet contains it; that interface is the WAN and the
    next-hop is the PE. Validated against live device:
      S* 0.0.0.0/0 via 62.22.251.49
      62.22.251.48/30 is directly connected, GigabitEthernet0/0/0
      => WAN=Gi0/0/0, PE=62.22.251.49
    Returns {'wan_interface': str, 'pe_ip': str, 'matched': bool}.
    """
    nh = parse_static_default_next_hop(show_ip_route)
    if not nh:
        return {'wan_interface': '', 'pe_ip': '', 'matched': False}

    # Scan connected (C/L) routes for a subnet containing the next-hop.
    for line in (show_ip_route or '').splitlines():
        m = re.search(
            r'(\d+\.\d+\.\d+\.\d+)/(\d+)\s+is directly connected,\s+(\S+)',
            line
        )
        if not m:
            continue
        net_ip, plen, iface = m.group(1), m.group(2), m.group(3)
        if re.match(r'^(Lo|Vl|Po|BDI|Tu|Nu)', iface, re.IGNORECASE):
            continue
        try:
            net = ipaddress.IPv4Network(f'{net_ip}/{plen}', strict=False)
            if ipaddress.IPv4Address(nh) in net:
                return {'wan_interface': iface, 'pe_ip': nh, 'matched': True}
        except Exception:
            continue
    return {'wan_interface': '', 'pe_ip': nh, 'matched': False}


# ---------------------------------------------------------------------------
# 8. derive_wan_interface_with_confidence  (3-signal algorithm)
# ---------------------------------------------------------------------------

def derive_wan_interface_with_confidence(
    show_ip_route, show_running, bgp_summary_text, show_int_desc,
    show_ip_int_brief=''
):
    """
    WAN identification (v11: 4 strong signals + 1 low-weight tie-breaker).
    Signal 1: default_route — exit interface in static default route
    Signal 2: bgp_subnet   — BGP neighbor on /30 or /31 subnet
    Signal 3: description  — WAN keyword in interface description
    Signal 4: circuit_id   — circuit-ID token (c + 7 digits) in description
    Tie-break: first_l3    — first physical L3 interface (LOW weight, never alone)

    HIGH confidence (bounce gate) = at least 2 STRONG signals agree on the same
    interface. The first_l3 tie-breaker never raises confidence to high on its own.

    Returns:
      {'interface': str, 'confidence': 'high'|'medium'|'low', 'signals': {...}}
    """
    signals = {
        'default_route': {'interface': '', 'fired': False, 'reason': ''},
        'bgp_subnet':    {'interface': '', 'fired': False, 'reason': ''},
        'description':   {'interface': '', 'fired': False, 'reason': ''},
        'circuit_id':    {'interface': '', 'fired': False, 'reason': ''},
        'first_l3':      {'interface': '', 'fired': False, 'reason': ''},
    }

    # Signal 1
    dr_iface = parse_default_route_interface(show_ip_route)
    if dr_iface:
        signals['default_route'] = {
            'interface': dr_iface, 'fired': True,
            'reason': f'Static default route (0.0.0.0/0) exit interface: {dr_iface}',
        }
    else:
        nh = parse_static_default_next_hop(show_ip_route)
        if nh:
            signals['default_route']['reason'] = (
                f'Default route is next-hop-only via {nh} — no exit interface specified'
            )
        else:
            signals['default_route']['reason'] = 'No static default route (0.0.0.0/0) found in routing table'

    # Signal 2
    bgp_iface = _find_bgp_wan_interface(bgp_summary_text, show_running)
    if bgp_iface:
        signals['bgp_subnet'] = {
            'interface': bgp_iface, 'fired': True,
            'reason': f'BGP neighbor resides on /30 or /31 subnet — WAN interface: {bgp_iface}',
        }
    else:
        signals['bgp_subnet']['reason'] = (
            'No BGP neighbor found on a /30 or /31 point-to-point subnet'
        )

    # Signal 3
    desc_iface = _find_wan_by_description(show_int_desc)
    if desc_iface:
        signals['description'] = {
            'interface': desc_iface, 'fired': True,
            'reason': f'WAN/MPLS/INET/Uplink keyword in interface description — interface: {desc_iface}',
        }
    else:
        signals['description']['reason'] = (
            'No WAN/MPLS/INET/Uplink/Internet keyword found in any interface description'
        )

    # Signal 4: circuit-ID token in description (STRONG)
    cid_iface = _find_wan_by_circuit_id(show_int_desc)
    if cid_iface:
        signals['circuit_id'] = {
            'interface': cid_iface, 'fired': True,
            'reason': f'Circuit-ID token (c+7 digits) in description — interface: {cid_iface}',
        }
    else:
        signals['circuit_id']['reason'] = 'No circuit-ID token (c followed by 7 digits) found in any description'

    # Tie-breaker: first physical L3 interface (LOW weight — never bounces alone)
    first_iface = _find_first_l3_interface(show_ip_int_brief)
    if first_iface:
        signals['first_l3'] = {
            'interface': first_iface, 'fired': True,
            'reason': f'First physical L3 interface with an IP: {first_iface} (low-weight tie-breaker)',
        }
    else:
        signals['first_l3']['reason'] = 'Could not determine first physical L3 interface'

    # STRONG signals decide confidence; first_l3 only breaks ties.
    strong = ['default_route', 'bgp_subnet', 'description', 'circuit_id']
    fired_ifaces = [signals[s]['interface'] for s in strong
                    if signals[s]['fired'] and signals[s]['interface']]

    if not fired_ifaces:
        # No strong signal. Fall back to first_l3 ONLY to name a candidate,
        # but confidence stays low → no bounce.
        if first_iface:
            return {'interface': first_iface, 'confidence': 'low', 'signals': signals}
        return {'interface': '', 'confidence': 'low', 'signals': signals}

    if len(fired_ifaces) == 1:
        # Single strong signal. If first_l3 agrees, still medium (not high) —
        # tie-breaker can corroborate but never manufacture HIGH on its own.
        return {'interface': fired_ifaces[0], 'confidence': 'medium', 'signals': signals}

    # 2+ strong signals fired — check agreement
    unique = set(_expand_iface(i).lower() for i in fired_ifaces)
    if len(unique) == 1:
        return {'interface': fired_ifaces[0], 'confidence': 'high', 'signals': signals}

    # Strong signals disagree — majority wins, drop to medium. Break exact ties
    # with the first_l3 hint if it matches one of the candidates.
    expanded = [_expand_iface(i).lower() for i in fired_ifaces]
    counts = Counter(expanded)
    top = counts.most_common()
    if len(top) > 1 and top[0][1] == top[1][1] and first_iface:
        fl = _expand_iface(first_iface).lower()
        if fl in expanded:
            for i in fired_ifaces:
                if _expand_iface(i).lower() == fl:
                    return {'interface': i, 'confidence': 'medium', 'signals': signals}
    best = top[0][0]
    for i in fired_ifaces:
        if _expand_iface(i).lower() == best:
            return {'interface': i, 'confidence': 'medium', 'signals': signals}

    return {'interface': fired_ifaces[0], 'confidence': 'medium', 'signals': signals}

# ---------------------------------------------------------------------------
# 9. BGP VRF map from running config
# ---------------------------------------------------------------------------

def parse_bgp_vrf_map(show_running_bgp_section):
    """
    Build {neighbor_ip: vrf_name} map from 'show running-config | section router bgp'.
    Returns dict — empty string for global (default VRF) neighbors.
    """
    vrf_map = {}
    if not show_running_bgp_section:
        return vrf_map

    current_vrf = ''
    for line in show_running_bgp_section.splitlines():
        stripped = line.strip()
        vrf_m = re.match(r'^address-family\s+\S+\s+vrf\s+(\S+)', stripped, re.IGNORECASE)
        if vrf_m:
            current_vrf = vrf_m.group(1)
            continue
        if re.match(r'^exit-address-family', stripped, re.IGNORECASE):
            current_vrf = ''
            continue
        nb_m = re.match(r'^neighbor\s+(\d+\.\d+\.\d+\.\d+)', stripped)
        if nb_m:
            ip = nb_m.group(1)
            # Only set vrf if not already recorded (global takes precedence? No — VRF-specific wins)
            vrf_map[ip] = current_vrf  # Overwrite: last address-family block wins

    return vrf_map

# ---------------------------------------------------------------------------
# 10. BGP summary parser
# ---------------------------------------------------------------------------

def parse_bgp_summary(bgp_all_summary_text):
    """
    Parse 'show ip bgp all summary' into list of neighbor state dicts.
    Returns: [{'neighbor': ip, 'as': str, 'state': str, 'established': bool, 'vrf': str}]
    """
    neighbors = []
    if not bgp_all_summary_text:
        return neighbors

    current_vrf = ''
    in_table = False

    for line in bgp_all_summary_text.splitlines():
        stripped = line.strip()

        # Detect VRF context (IOS/IOS-XE: "For vrf: TEST", IOS-XR: "VRF: TEST")
        vrf_m = re.search(r'(?:[Ff]or vrf|VRF):\s*(\S+)', stripped)
        if vrf_m:
            vrf_name = vrf_m.group(1)
            current_vrf = '' if vrf_name.lower() in ('default', 'global') else vrf_name
            in_table = False
            continue

        # Reset to global on top-level address family without VRF qualifier
        if re.search(r'[Ff]or address family:\s*IPv4 Unicast\s*$', stripped):
            current_vrf = ''
            in_table = False
            continue

        if re.search(r'Neighbor\s+V\s+AS', stripped):
            in_table = True
            continue

        if not in_table:
            continue

        # Capture the full state field including multi-word states
        # like "Idle (Admin)", "No Neg", "Idle (PfxCt)"
        # Pattern: IP  V  AS  MsgRcvd  MsgSent  TblVer  InQ  OutQ  Up/Down  State/PfxRcd
        m = re.match(
            r'^\s*(\d+\.\d+\.\d+\.\d+)\s+\d+\s+(\d+)\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+(.+?)\s*$',
            line
        )
        if m:
            nb_ip = m.group(1)
            as_num = m.group(2)
            state_field = m.group(3).strip()
            established = state_field.isdigit()
            # Admin-shutdown: "Idle (Admin)" — must NOT be cleared
            admin_down = 'admin' in state_field.lower()
            neighbors.append({
                'neighbor': nb_ip,
                'as': as_num,
                'state': 'Established' if established else state_field,
                'established': established,
                'admin_down': admin_down,
                'vrf': current_vrf,
            })

    return neighbors

# ---------------------------------------------------------------------------
# 11. find_stuck_bgp_neighbors
# ---------------------------------------------------------------------------

def find_stuck_bgp_neighbors(bgp_all_summary_text, bgp_vrf_map):
    """
    Find non-Established BGP neighbors.
    bgp_vrf_map: {neighbor_ip: vrf} from parse_bgp_vrf_map.

    Returns list of {neighbor, vrf, state, as_number, hint, admin_down}.

    SAFETY: admin_down=True neighbors are included in the list BUT must NOT
    be cleared — they were intentionally shut. The YAML loop must filter them:
      loop: "{{ stuck_neighbors | rejectattr('admin_down', 'equalto', true) | list }}"
    """
    stuck = []
    all_neighbors = parse_bgp_summary(bgp_all_summary_text)

    for nb in all_neighbors:
        if nb['established']:
            continue
        vrf = bgp_vrf_map.get(nb['neighbor'], nb['vrf'])
        admin_down = nb.get('admin_down', False)
        stuck.append({
            'neighbor': nb['neighbor'],
            'as_number': nb['as'],
            'vrf': vrf,
            'state': nb['state'],
            'hint': bgp_state_hint(nb['state']),
            'admin_down': admin_down,   # True = Idle (Admin) — do NOT clear
        })

    return stuck

# ---------------------------------------------------------------------------
# 12. bgp_state_hint
# ---------------------------------------------------------------------------

def bgp_state_hint(state):
    """Per-state root-cause hint per MOP."""
    _hints = {
        'idle':       'BGP is not attempting to connect. Possible causes: no route to peer, '
                      'reset by operator, or local policy blocking the session.',
        'active':     'BGP is attempting TCP connection but failing. Possible causes: '
                      'peer unreachable, ACL blocking TCP/179, or peer BGP not running.',
        'connect':    'TCP SYN sent, awaiting SYN-ACK. Likely transient or peer TCP stack issue.',
        'opensent':   'TCP connected, BGP OPEN sent. Awaiting peer OPEN — '
                      'possible BGP version or capability mismatch.',
        'openconfirm':'BGP OPEN received and replied. Hold timer negotiation in progress.',
        'established':'Session is UP and exchanging prefixes.',
        'deleted':    'Neighbor configuration deleted or being removed.',
        'unknown':    'State unrecognized — check full "show ip bgp neighbors" output.',
    }
    return _hints.get(state.lower(), f'State: {state} — check "show ip bgp neighbors {{}}" for detail.')

# ---------------------------------------------------------------------------
# 13. build_bgp_clear_command
# ---------------------------------------------------------------------------

def build_bgp_clear_command(neighbor_ip, vrf, platform='ios'):
    """
    Build platform-aware BGP clear command.
    neighbor_ip must be a string IP address (not a dict).

    Platform command matrix:
      ios / ios_xe : clear ip bgp <ip> [vrf <vrf>]
      ios_xr       : clear bgp vrf <vrf> <ip>    (VRF)
                     clear bgp <ip>              (global)

    NOTE: On IOS 15.x, 'clear ip bgp <ip>' (without vrf qualifier) also works
    for VRF neighbors when the neighbor IP is unique across all VRFs.
    The explicit 'vrf' qualifier is used on IOS-XE for precision.
    """
    if not isinstance(neighbor_ip, str):
        raise ValueError(
            f'build_bgp_clear_command expects string IP, got {type(neighbor_ip)}: {neighbor_ip}'
        )

    ip = neighbor_ip.strip()
    if not re.match(r'^\d+\.\d+\.\d+\.\d+$', ip):
        raise ValueError(f'Invalid neighbor IP: {ip!r}')

    has_vrf = bool(vrf and vrf.lower() not in ('', 'default', 'global'))

    if str(platform) == 'ios_xr':
        # IOS-XR: "clear bgp" not "clear ip bgp"
        if has_vrf:
            return f'clear bgp vrf {vrf} {ip}'
        return f'clear bgp {ip}'

    # ios and ios_xe — same syntax
    vrf_part = f' vrf {vrf}' if has_vrf else ''
    return f'clear ip bgp {ip}{vrf_part}'


# ---------------------------------------------------------------------------
# NEW v6: build_bgp_vrf_summary_command — platform-aware VRF BGP summary
# ---------------------------------------------------------------------------

def build_bgp_vrf_summary_command(vrf, platform='ios'):
    """
    Return the correct BGP VRF summary command for the given platform.
    Used in bgp_remediation.yaml VRF cross-check (task 1600).

    ios    : show ip bgp vpnv4 vrf <vrf> summary
    ios_xe : show ip bgp vrf <vrf> summary
    ios_xr : show bgp vrf <vrf> summary
    """
    if not vrf or str(vrf).lower() in ('', 'default', 'global'):
        if str(platform) == 'ios_xr':
            return 'show bgp summary'
        return 'show ip bgp summary'

    if str(platform) == 'ios_xr':
        return f'show bgp vrf {vrf} summary'
    if str(platform) == 'ios':
        return f'show ip bgp vpnv4 vrf {vrf} summary'
    # ios_xe (and unknown — default to XE syntax which is more modern)
    return f'show ip bgp vrf {vrf} summary'


# ---------------------------------------------------------------------------
# NEW v6: get_bgp_discovery_commands — full platform-aware BGP discovery list
# ---------------------------------------------------------------------------

def get_bgp_discovery_commands(platform='ios'):
    """
    Return list of BGP summary commands covering global + all VRF sessions.

    ios    : ['show ip bgp summary', 'show ip bgp vpnv4 all summary']
             Classic IOS may not include VRF sessions in 'show ip bgp all summary'
             so we explicitly use vpnv4 all to catch all VRF neighbors.
    ios_xe : ['show ip bgp all summary']
             Single command covers global + all VRFs.
    ios_xr : ['show bgp summary', 'show bgp all summary']
             'ip bgp' prefix not valid on XR.
    """
    if str(platform) == 'ios_xr':
        return ['show bgp summary', 'show bgp all summary']
    if str(platform) == 'ios':
        return ['show ip bgp summary', 'show ip bgp vpnv4 all summary']
    # ios_xe
    return ['show ip bgp all summary']


# ---------------------------------------------------------------------------
# NEW v6: merge_bgp_summary_outputs — combine outputs into single parse string
# ---------------------------------------------------------------------------

def merge_bgp_summary_outputs(outputs_dict, platform='ios'):
    """
    Given the outputs dict from device_ssh.py, extract and combine the
    BGP summary text appropriate for the platform into a single string
    for parse_bgp_summary to process.
    """
    if not isinstance(outputs_dict, dict):
        return ''

    if str(platform) == 'ios_xr':
        return (outputs_dict.get('show bgp all summary', '')
                or outputs_dict.get('show bgp summary', ''))

    if str(platform) == 'ios':
        # vpnv4 all includes all VRF sessions; global catches non-VPN global peers
        vpnv4 = outputs_dict.get('show ip bgp vpnv4 all summary', '')
        global_v4 = outputs_dict.get('show ip bgp summary', '')
        parts = [p for p in [vpnv4, global_v4] if p]
        return '\n'.join(parts)

    # ios_xe
    return (outputs_dict.get('show ip bgp all summary', '')
            or outputs_dict.get('show ip bgp summary', ''))


# ---------------------------------------------------------------------------
# 14. compute_other_end_ip  (PE IP from /30 or /31)
# ---------------------------------------------------------------------------

def compute_other_end_ip(ip, mask):
    """
    For a /30 or /31 link, return the other-end IP (PE side).
    Returns empty string if subnet is wider than /30.
    """
    if not ip or not mask:
        return ''
    try:
        net = ipaddress.IPv4Network(f'{ip}/{mask}', strict=False)
        prefix_len = net.prefixlen
        if prefix_len == 31:
            hosts = list(net.hosts()) if net.num_addresses > 2 else list(net)
            ce_addr = ipaddress.IPv4Address(ip)
            others = [h for h in hosts if h != ce_addr]
            return str(others[0]) if others else ''
        if prefix_len == 30:
            hosts = list(net.hosts())
            ce_addr = ipaddress.IPv4Address(ip)
            others = [h for h in hosts if h != ce_addr]
            return str(others[0]) if others else ''
    except Exception:
        pass
    return ''

# ---------------------------------------------------------------------------
# 15. derive_pe_ip  (three-method derivation with confidence)
# ---------------------------------------------------------------------------

def derive_pe_ip(wan_ip, wan_mask, bgp_neighbors_text, static_nh):
    """
    Derive PE IP using three methods:
    1. /30 or /31 subnet arithmetic (CE WAN IP → PE IP)
    2. Static default next-hop
    3. BGP neighbor on WAN subnet

    Returns {'pe_ip': str, 'confidence': 'high'|'medium'|'low'|'none', 'method': str}
    """
    # Method 1: subnet arithmetic
    if wan_ip and wan_mask:
        try:
            net = ipaddress.IPv4Network(f'{wan_ip}/{wan_mask}', strict=False)
            if net.prefixlen in (30, 31):
                pe_ip = compute_other_end_ip(wan_ip, wan_mask)
                if pe_ip:
                    return {
                        'pe_ip': pe_ip,
                        'confidence': 'high',
                        'method': f'/{"30" if net.prefixlen == 30 else "31"} subnet arithmetic — CE: {wan_ip}, PE: {pe_ip}',
                    }
        except Exception:
            pass

    # Method 2: static default next-hop
    if static_nh and re.match(r'^\d+\.\d+\.\d+\.\d+$', static_nh.strip()):
        return {
            'pe_ip': static_nh.strip(),
            'confidence': 'medium',
            'method': f'Static default route next-hop: {static_nh}',
        }

    # Method 3: BGP neighbor on WAN subnet
    if wan_ip and wan_mask and bgp_neighbors_text:
        try:
            wan_net = ipaddress.IPv4Network(f'{wan_ip}/{wan_mask}', strict=False)
            for line in bgp_neighbors_text.splitlines():
                m = re.match(r'^\s*(\d+\.\d+\.\d+\.\d+)', line)
                if m:
                    candidate = ipaddress.IPv4Address(m.group(1))
                    if candidate in wan_net and str(candidate) != wan_ip:
                        return {
                            'pe_ip': str(candidate),
                            'confidence': 'medium',
                            'method': f'BGP neighbor {candidate} on WAN subnet {wan_net}',
                        }
        except Exception:
            pass

    return {'pe_ip': '', 'confidence': 'none', 'method': 'PE IP could not be derived by any available method'}

# ---------------------------------------------------------------------------
# 16. replace_update_with_notify  (v4: added execute→run)
# ---------------------------------------------------------------------------

def replace_update_with_notify(text):
    """
    VBSM word sanitizer.
    VBSM strips certain words from work_notes:
      'update'  → 'notify'
      'execute' → 'run'
    Apply these replacements proactively so output.dat is WYSIWYG.
    """
    if not text:
        return text
    result = re.sub(r'\bupdate\b', 'notify', text, flags=re.IGNORECASE)
    result = re.sub(r'\bexecute\b', 'run', result, flags=re.IGNORECASE)
    return result

# ---------------------------------------------------------------------------
# 17. diff_running_configs  (NEW v5)
# ---------------------------------------------------------------------------

def diff_running_configs(pre_config, post_config):
    """
    Produce unified diff of pre and post running-config.
    Returns human-readable diff string, or no-change message.
    """
    if not pre_config and not post_config:
        return 'PRE and POST configs both empty — cannot produce diff.'

    pre_lines = (pre_config or '').splitlines(keepends=True)
    post_lines = (post_config or '').splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        pre_lines,
        post_lines,
        fromfile='running-config (pre-remediation)',
        tofile='running-config (post-remediation)',
        lineterm='',
    ))

    if not diff:
        return 'NO CONFIGURATION CHANGE — Running-config identical before and after automation.'

    return ''.join(diff)

# ---------------------------------------------------------------------------
# 18. format_wan_identification_result  (NEW v5)
# ---------------------------------------------------------------------------

def format_wan_identification_result(wan_result):
    """
    Format WAN identification result into NOC-readable block.
    wan_result: dict from derive_wan_interface_with_confidence.
    """
    iface = wan_result.get('interface', '')
    confidence = wan_result.get('confidence', 'low')
    signals = wan_result.get('signals', {})

    lines = []
    if iface:
        lines.append(f'[WAN INTERFACE] STATUS: IDENTIFIED')
        lines.append(f'Interface : {iface}')
        lines.append(f'Confidence: {confidence.upper()}')
    else:
        lines.append(f'[WAN INTERFACE] STATUS: NOT IDENTIFIED')
        lines.append(f'Confidence: {confidence.upper()} — Automation cannot safely determine WAN interface.')

    lines.append('')
    lines.append('Signal evaluation:')
    for sig_name, sig_data in signals.items():
        fired = sig_data.get('fired', False)
        reason = sig_data.get('reason', '')
        iface_found = sig_data.get('interface', '')
        mark = 'FIRED' if fired else 'not fired'
        sig_line = f'  {sig_name:<18}: [{mark}]'
        if iface_found:
            sig_line += f' → {iface_found}'
        lines.append(sig_line)
        lines.append(f'    Reason: {reason}')

    return '\n'.join(lines)

# ---------------------------------------------------------------------------
# 19. parse_ping_result
# ---------------------------------------------------------------------------

def parse_ping_result(ping_json):
    """Parse ping.py JSON output. Returns {'reachable': bool, 'loss': int, 'output': str}."""
    if isinstance(ping_json, str):
        ping_json = safe_json_parse(ping_json)
    loss = ping_json.get('packet_loss', 100)
    return {
        'reachable': loss < 100,
        'loss': loss,
        'output': ping_json.get('output', ''),
        'error': ping_json.get('error', ''),
    }

# ---------------------------------------------------------------------------
# 20. extract_bgp_neighbor_section
# ---------------------------------------------------------------------------

def extract_bgp_neighbor_section(show_running_bgp, neighbor_ip):
    """Extract config lines for a specific BGP neighbor from running-config section."""
    lines = []
    in_block = False
    for line in show_running_bgp.splitlines():
        stripped = line.strip()
        if f'neighbor {neighbor_ip}' in stripped:
            lines.append(stripped)
        elif stripped.startswith('neighbor') and neighbor_ip not in stripped and in_block:
            in_block = False
    return '\n'.join(lines)

# ---------------------------------------------------------------------------
# 21. derive_shortname_from_neid
# ---------------------------------------------------------------------------

def derive_shortname_from_neid(dns_entity_name):
    """Extract customer shortname from NEID (first hyphen-delimited segment)."""
    if not dns_entity_name:
        return ''
    return dns_entity_name.split('-')[0].lower()

# ---------------------------------------------------------------------------
# 22. derive_site_group
# ---------------------------------------------------------------------------

def derive_site_group(dns_entity_name, suffix_chars=3):
    """Compute site group by stripping last N chars from NEID (for ESP partner discovery)."""
    if not dns_entity_name or len(dns_entity_name) <= suffix_chars:
        return dns_entity_name or ''
    return dns_entity_name[:-suffix_chars]

# ---------------------------------------------------------------------------
# 23. normalize_description
# ---------------------------------------------------------------------------

def normalize_description(raw_description):
    r"""
    Normalize Description field: replace literal '\n' with actual newlines.
    Jenkins passes Description as a single-line string with \n tokens.
    """
    if not raw_description:
        return ''
    return raw_description.replace('\\n', '\n')

# ---------------------------------------------------------------------------
# 24. extract_neid_from_description
# ---------------------------------------------------------------------------

def extract_neid_from_description(description_normalized):
    """Extract NEID from normalized description text."""
    m = re.search(r'NEID:\s*(\S+)', description_normalized, re.IGNORECASE)
    return m.group(1) if m else ''

# ---------------------------------------------------------------------------
# 25. is_bgp_active
# ---------------------------------------------------------------------------

def is_bgp_active(bgp_all_summary_text):
    """Return True if BGP is running (not the '% BGP not active' response)."""
    if not bgp_all_summary_text:
        return False
    return 'bgp not active' not in bgp_all_summary_text.lower()

# ---------------------------------------------------------------------------
# 26. check_privilege_denied
# ---------------------------------------------------------------------------

def check_privilege_denied(device_ssh_result):
    """Return True if device_ssh.py result indicates privilege denied."""
    if isinstance(device_ssh_result, str):
        device_ssh_result = safe_json_parse(device_ssh_result)
    return device_ssh_result.get('privilege_denied', False)

# ---------------------------------------------------------------------------
# 27. extract_ssh_output
# ---------------------------------------------------------------------------

def extract_ssh_output(device_ssh_result, command=None):
    """
    Extract command output from device_ssh.py JSON result.
    If command is specified, returns that command's output from 'outputs' dict.
    Otherwise returns single 'output' field.
    """
    if isinstance(device_ssh_result, str):
        device_ssh_result = safe_json_parse(device_ssh_result)

    if command:
        return device_ssh_result.get('outputs', {}).get(command, '')

    return device_ssh_result.get('output', '') or ''

# ---------------------------------------------------------------------------
# 28. summarize_phase_results
# ---------------------------------------------------------------------------

def summarize_phase_results(phase_results):
    """Format phase_results dict into NOC-readable summary."""
    if not phase_results:
        return 'No phase results recorded.'
    lines = []
    for phase, status in sorted(phase_results.items()):
        mark = '✓' if status == 'ok' else ('↷' if status == 'skipped' else '✗')
        lines.append(f'  {mark} {phase}: {status}')
    return '\n'.join(lines)

# ---------------------------------------------------------------------------
# 29. redact_password
# ---------------------------------------------------------------------------

def redact_password(text):
    """Redact common password/secret patterns from output."""
    if not text:
        return text
    text = re.sub(r'(password\s+)\S+', r'\1[REDACTED]', text, flags=re.IGNORECASE)
    text = re.sub(r'(secret\s+\d+\s+)\S+', r'\1[REDACTED]', text, flags=re.IGNORECASE)
    return text

# ---------------------------------------------------------------------------
# 30. precheck_aborted
# ---------------------------------------------------------------------------

def precheck_aborted(device_ssh_result):
    """Return True if device_ssh.py aborted due to pre_check gate failure."""
    if isinstance(device_ssh_result, str):
        device_ssh_result = safe_json_parse(device_ssh_result)
    return device_ssh_result.get('pre_check_failed', False)

# ---------------------------------------------------------------------------
# FilterModule registration
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# NEW v7: extract_bgp_update_source
# ---------------------------------------------------------------------------
def extract_bgp_update_source(bgp_config_text, neighbor_ip):
    """
    Parse 'show running-config | section router bgp' to find the
    update-source interface for a specific BGP neighbor.
    Returns interface name or '' (empty = use physical exit interface).
    MOP logic: neighbor X update-source <intf> -> ping X source <intf>
    """
    if not bgp_config_text or not neighbor_ip:
        return ''
    ip = str(neighbor_ip).strip()
    for line in str(bgp_config_text).splitlines():
        m = re.match(
            r'\s*neighbor\s+' + re.escape(ip) + r'\s+update-source\s+(\S+)',
            line
        )
        if m:
            return m.group(1)
    return ''


# ---------------------------------------------------------------------------
# NEW v7: verify_bgp_neighbor_config
# ---------------------------------------------------------------------------
def verify_bgp_neighbor_config(bgp_config_text, stuck_neighbors):
    """
    After failed BGP clear, verify config for each stuck neighbor.
    Checks: neighbor present, remote-AS, update-source, shutdown flag.
    Returns list of dicts with 'verdict' key for NOC guidance.
    """
    if not bgp_config_text or not stuck_neighbors:
        return []
    results = []
    for nb in stuck_neighbors:
        ip = str(nb.get('neighbor', '')).strip()
        if not ip:
            continue
        in_cfg = remote_as = update_src = ''
        shutdown_cfg = False
        for line in str(bgp_config_text).splitlines():
            s = line.strip()
            if 'neighbor ' + ip not in s:
                continue
            in_cfg = True
            m = re.match(r'neighbor\s+\S+\s+remote-as\s+(\d+)', s)
            if m:
                remote_as = m.group(1)
            m = re.match(r'neighbor\s+\S+\s+update-source\s+(\S+)', s)
            if m:
                update_src = m.group(1)
            if 'shutdown' in s:
                shutdown_cfg = True
        verdict = (
            'NEIGHBOR_NOT_IN_CONFIG'    if not in_cfg else
            'ADMIN_SHUTDOWN_IN_CONFIG'  if shutdown_cfg else
            'MISSING_REMOTE_AS'         if not remote_as else
            'CONFIG_LOOKS_CORRECT'
        )
        results.append({
            'neighbor': ip,
            'vrf': nb.get('vrf', ''),
            'state': nb.get('state', ''),
            'in_config': bool(in_cfg),
            'remote_as': remote_as,
            'update_source': update_src,
            'shutdown_in_config': shutdown_cfg,
            'verdict': verdict,
        })
    return results


# ---------------------------------------------------------------------------
# NEW v7: build_bgp_underlay_commands
# ---------------------------------------------------------------------------
def build_bgp_underlay_commands(nb, wan_interface, platform='ios'):
    """
    Build BGP underlay reachability commands for one stuck neighbor.
    MOP: ping <neighbor> source <update-source or WAN>, traceroute, show arp.
    """
    if not isinstance(nb, dict):
        return []
    neighbor_ip = str(nb.get('neighbor', '')).strip()
    vrf         = str(nb.get('vrf', '')).strip()
    has_vrf     = bool(vrf and vrf.lower() not in ('', 'default', 'global'))
    if not neighbor_ip:
        return []
    update_source = str(nb.get('update_source', '')).strip()
    source_intf   = update_source or (str(wan_interface).strip() if wan_interface else '')
    cmds = []
    if str(platform) == 'ios_xr':
        pfx = f'vrf {vrf} ' if has_vrf else ''
        cmds.append(f'ping {pfx}{neighbor_ip} count 5 timeout 3')
        cmds.append(f'traceroute {pfx}{neighbor_ip} timeout 1 maxttl 5')
        cmds.append(f'show arp {pfx}| utility grep {neighbor_ip}')
        cmds.append(f'show route {pfx}{neighbor_ip}')
    else:
        if has_vrf:
            cmds.append(f'ping vrf {vrf} {neighbor_ip} repeat 5 timeout 3')
            cmds.append(f'traceroute vrf {vrf} {neighbor_ip} timeout 1 probe 1 ttl 1 5')
            cmds.append(f'show ip arp vrf {vrf} | include {neighbor_ip}')
            cmds.append(f'show ip route vrf {vrf} {neighbor_ip}')
        else:
            src = f' source {source_intf}' if source_intf else ''
            cmds.append(f'ping {neighbor_ip}{src} repeat 5 timeout 3')
            cmds.append(f'traceroute {neighbor_ip} timeout 1 probe 1 ttl 1 5')
            cmds.append(f'show ip arp | include {neighbor_ip}')
            cmds.append(f'show ip route {neighbor_ip}')
    return cmds


# ---------------------------------------------------------------------------
# NEW v8: build_bgp_neighbor_ping_cmd — GAP-2 fix
# ---------------------------------------------------------------------------
def build_bgp_neighbor_ping_cmd(nb, platform='ios'):
    """Build platform/VRF-aware ping command for a BGP neighbor.
    Used post-clear to ping neighbor IP (not MgmtIP) per MOP."""
    if not isinstance(nb, dict):
        return ''
    ip  = str(nb.get('neighbor', '')).strip()
    vrf = str(nb.get('vrf', '')).strip()
    has_vrf = bool(vrf and vrf.lower() not in ('', 'default', 'global'))
    if not ip:
        return ''
    if str(platform) == 'ios_xr':
        return f'ping vrf {vrf} {ip} count 5 timeout 3' if has_vrf else f'ping {ip} count 5 timeout 3'
    return f'ping vrf {vrf} {ip} repeat 5 timeout 3' if has_vrf else f'ping {ip} repeat 5 timeout 3'


# ---------------------------------------------------------------------------
# NEW v9: evaluate_underlay_reachability — GAP-1 gating
# Match each stuck neighbor to its underlay ping output (robust to the
# "source <intf>" variant and VRF), decide L3-reachable, and carry the
# matched ping/traceroute/arp text so the log task does not reconstruct keys.
# ---------------------------------------------------------------------------
def evaluate_underlay_reachability(stuck_neighbors, underlay_outputs):
    """
    Returns one dict per non-admin-down neighbor:
      {neighbor, vrf, as_number, state, admin_down, update_source,
       reachable (bool), ping_text, tracert_text, arp_text}
    reachable=True only when the ping output shows a non-zero success rate.
    """
    if not stuck_neighbors:
        return []
    outputs = underlay_outputs if isinstance(underlay_outputs, dict) else {}

    def _match(prefixes, ip, vrf_token):
        for key, val in outputs.items():
            k = key.strip()
            if not any(k.startswith(p) for p in prefixes):
                continue
            if ip not in k:
                continue
            if vrf_token and vrf_token not in k:
                continue
            if (not vrf_token) and ' vrf ' in k:
                continue
            return val
        return ''

    def _reachable(ping_text):
        t = ping_text or ''
        if 'Success rate is 0' in t:
            return False
        if 'Success rate is' in t:        # any non-zero percentage
            return True
        if '!!!' in t:
            return True
        # weak fallback: a bare '!' with no success-rate line
        if '!' in t and 'Success rate' not in t:
            return True
        return False

    results = []
    for nb in stuck_neighbors:
        if not isinstance(nb, dict):
            continue
        if nb.get('admin_down', False):
            continue
        ip  = str(nb.get('neighbor', '')).strip()
        vrf = str(nb.get('vrf', '')).strip()
        has_vrf = bool(vrf and vrf.lower() not in ('', 'default', 'global'))
        vtok = f'vrf {vrf}' if has_vrf else ''
        ping_text    = _match(('ping',), ip, vtok)
        tracert_text = _match(('traceroute',), ip, vtok)
        arp_text     = _match(('show ip arp', 'show arp'), ip, vtok)
        results.append({
            'neighbor':      ip,
            'vrf':           vrf,
            'as_number':     nb.get('as_number', ''),
            'state':         nb.get('state', ''),
            'state_hint':    bgp_state_hint(nb.get('state', '')),
            'admin_down':    False,
            'update_source': nb.get('update_source', ''),
            'reachable':     _reachable(ping_text),
            'ping_text':     ping_text or '(not executed)',
            'tracert_text':  tracert_text or '(not executed)',
            'arp_text':      arp_text or '(no ARP entry)',
        })
    return results


# ---------------------------------------------------------------------------
# v11: VRRP/HSRP virtual-IP parsing + primary LAN IP derivation (jump-host)
# ---------------------------------------------------------------------------

def find_partner_candidates(devices, primary_neid, primary_ip):
    """
    Find HA partner router candidates from ESP device list.

    Three confirmed ESP API facts (validated in SIT):
      1. shortName filter works  — returns all customer devices
      2. deviceType filter DOES NOT work — returns all 313 regardless
      3. dnsShortName filter DOES NOT work — returns all 313 regardless
    All filtering must be done in Python on the returned list.

    Matching rule: partner must share the first two hyphen-delimited NEID
    tokens with the primary. This is the production HA pair convention.
      primary = deapega-r25pega-2989417e001
      prefix  = deapega-r25pega-          (first two tokens + hyphen)
      partner = deapega-r25pega-3106229e001  ← matches

    Handles both response shapes:
      wrapped:   {"device": {"dnsEntityName": ..., "mgmtIPAddress": ...}}
      unwrapped: {"dnsEntityName": ..., "mgmtIPAddress": ...}

    Excludes: primary itself (by NEID and IP), unmanaged devices,
              known non-router device types.
    """
    _SKIP_TYPES = frozenset([
        'vmanage', 'vsmart', 'vbond', 'director', 'controller',
        'modem', 'switch', 'ap', 'access point', 'firewall',
        'wlc', 'access-point', 'wireless',
    ])
    parts = str(primary_neid).split('-')
    # Use first two hyphen tokens as the site prefix
    dns_prefix = '-'.join(parts[:2]) + '-'  # e.g. "deapega-r25pega-"

    result = []
    for item in (devices or []):
        if not isinstance(item, dict):
            continue
        # Handle both wrapped and unwrapped ESP response shapes
        dev = item.get('device', item)
        if not isinstance(dev, dict):
            continue
        neid    = dev.get('dnsEntityName', '')
        ip      = dev.get('mgmtIPAddress', '')
        dtype   = dev.get('deviceType', '').lower().strip()
        managed = dev.get('isManaged', False)

        # Skip the primary device itself
        if neid == primary_neid or ip == primary_ip:
            continue
        # Skip unmanaged devices
        if not managed:
            continue
        # Skip known non-router device types
        if any(kw in dtype for kw in _SKIP_TYPES):
            continue
        # Must share the site NEID prefix (first two hyphen tokens)
        if not neid.startswith(dns_prefix):
            continue
        result.append(dev)
    return result


def reject_non_router_devices(candidates):
    """
    Filter out non-router device types from ESP inventory candidate list.

    The ESP deviceType URL filter is confirmed non-functional — it returns all
    devices regardless of the parameter. This function provides the Python-side
    filtering that the URL param was supposed to give, so that switches,
    firewalls, controllers, etc. are never selected as partner router candidates.

    Handles both flat response shape (deviceType at top level) and nested shape
    (device.deviceType sub-object) since the exact ESP response format is
    environment-dependent.
    """
    _SKIP_TYPES = frozenset([
        'vmanage', 'vsmart', 'vbond', 'director', 'controller',
        'modem', 'switch', 'ap', 'access point', 'firewall',
        'wlc', 'access-point', 'wireless',
    ])
    result = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        # Flat shape: item has 'deviceType' directly
        # Nested shape: item has 'device' sub-dict with 'deviceType'
        dtype = (
            item.get('deviceType', '')
            or (item.get('device') or {}).get('deviceType', '')
        ).lower().strip()
        if any(kw in dtype for kw in _SKIP_TYPES):
            continue
        result.append(item)
    return result


def parse_vty_acl(vty_section, access_class_lines, ip_access_lists, secondary_lan_ip=''):
    """
    Parse VTY/ACL config gathered from the SECONDARY router to explain a refused
    SSH jump to the primary. The primary's own ACL is unreachable (that's why the
    jump failed), but managed CE pairs are provisioned from the same template, so
    the secondary's VTY ACL is the best available evidence of the site policy.

    Inputs (all raw CLI text from the secondary):
      vty_section        : 'show running-config | section vty'
      access_class_lines : 'show running-config | include access-class'
      ip_access_lists    : 'show ip access-lists'

    Returns dict:
      {vty_lines, access_class_in, access_class_out, acl_name,
       acl_rules, secondary_permitted, summary}
    """
    out = {
        'vty_lines': [], 'access_class_in': '', 'access_class_out': '',
        'acl_name': '', 'acl_rules': [], 'secondary_permitted': None, 'summary': '',
    }

    # VTY line ranges present (e.g. "line vty 0 4")
    for ln in (vty_section or '').splitlines():
        m = re.match(r'\s*(line vty\s+\d+(?:\s+\d+)?)', ln, re.I)
        if m:
            out['vty_lines'].append(m.group(1).strip())

    # access-class <name|num> in|out  (the ACL bound to VTY)
    for ln in ((access_class_lines or '') + '\n' + (vty_section or '')).splitlines():
        m = re.search(r'access-class\s+(\S+)\s+(in|out)', ln, re.I)
        if m:
            name, direction = m.group(1), m.group(2).lower()
            if direction == 'in' and not out['access_class_in']:
                out['access_class_in'] = name
                out['acl_name'] = name      # inbound is the one that gates SSH to the VTY
            elif direction == 'out' and not out['access_class_out']:
                out['access_class_out'] = name

    # If only an outbound class exists, still surface it as the acl_name fallback
    if not out['acl_name'] and out['access_class_out']:
        out['acl_name'] = out['access_class_out']

    # Extract the rules for the bound ACL from 'show ip access-lists'
    if out['acl_name'] and ip_access_lists:
        capturing = False
        for ln in ip_access_lists.splitlines():
            header = re.match(r'^(?:Standard|Extended)?\s*IP access list\s+(\S+)', ln, re.I) \
                or re.match(r'^ip access-list\s+\w+\s+(\S+)', ln, re.I)
            if header:
                capturing = (header.group(1) == out['acl_name'])
                continue
            if capturing:
                r = ln.strip()
                if r and (r.startswith(('permit', 'deny')) or re.match(r'^\d+\s+(permit|deny)', r)):
                    out['acl_rules'].append(r)

    # Does the secondary's own LAN IP appear permitted? (heuristic: if the
    # secondary can be reached but the primary refuses, the ACL likely permits
    # a mgmt range that does not include the secondary's jump source.)
    sec = str(secondary_lan_ip).strip()
    if out['acl_rules'] and sec:
        permit_hit = any('permit' in r and (sec in r) for r in out['acl_rules'])
        deny_hit = any('deny' in r and (sec in r) for r in out['acl_rules'])
        if permit_hit and not deny_hit:
            out['secondary_permitted'] = True
        elif deny_hit:
            out['secondary_permitted'] = False

    # Human summary line for the NOC
    parts = []
    if out['vty_lines']:
        parts.append('VTY: ' + ', '.join(out['vty_lines']))
    if out['acl_name']:
        parts.append(f"access-class {out['acl_name']} in" if out['access_class_in']
                     else f"access-class {out['acl_name']}")
    else:
        parts.append('no access-class found on secondary VTY (primary policy may still differ)')
    if out['acl_rules']:
        parts.append(f"{len(out['acl_rules'])} ACL rule(s) captured from secondary")
    out['summary'] = '; '.join(parts)
    return out


def parse_fhrp_state(show_vrrp_brief, show_standby_brief='', secondary_lan_ip=''):
    """
    Parse VRRP ('show vrrp brief') or HSRP ('show standby brief') run on the
    secondary CE. Returns a dict:
      {vip, active_ip, standby_ip, protocol, secondary_is_active}

    show standby brief (HSRP):
      Interface Grp Pri P State   Active         Standby        Virtual IP
      Gi0/0     1   90  P Standby 192.168.31.75  local          192.168.31.125
    show vrrp brief (VRRP):
      Interface Grp Pri Time Own Pre State  Master addr    Group addr
      Gi0/0     1   100 ...      Y  Master  192.168.31.75  192.168.31.125

    'local' denotes the secondary itself. For HSRP the last IP is the VIP and
    the Active column points at the primary. For VRRP the last IP is the VIP
    and the Master addr is the primary.
    """
    result = {'vip': '', 'active_ip': '', 'standby_ip': '',
              'protocol': '', 'secondary_is_active': False}

    def _resolve_local(token, sec_ip):
        return sec_ip if token.lower() == 'local' else token

    if show_standby_brief:
        for line in show_standby_brief.splitlines():
            if not re.match(r'^\s*(Gi|Te|Fa|Et|Vl|Po|Hu|Fo)\S*\s+\d+', line):
                continue
            cols = line.split()
            ips = [c for c in cols if re.match(r'^\d+\.\d+\.\d+\.\d+$', c)]
            has_local = 'local' in [c.lower() for c in cols]
            state = next((c for c in cols if c.lower() in ('active', 'standby', 'init', 'listen', 'speak')), '')
            if not ips and not has_local:
                continue
            result['protocol'] = 'hsrp'
            result['vip'] = ips[-1] if ips else ''
            try:
                vip_idx = cols.index(result['vip'])
                active_tok = cols[vip_idx - 2]
                standby_tok = cols[vip_idx - 1]
                result['active_ip'] = _resolve_local(active_tok, secondary_lan_ip)
                result['standby_ip'] = _resolve_local(standby_tok, secondary_lan_ip)
            except (ValueError, IndexError):
                pass
            result['secondary_is_active'] = state.lower() == 'active'
            return result

    if show_vrrp_brief:
        for line in show_vrrp_brief.splitlines():
            if not re.match(r'^\s*(Gi|Te|Fa|Et|Vl|Po|Hu|Fo)\S*\s+\d+', line):
                continue
            cols = line.split()
            ips = [c for c in cols if re.match(r'^\d+\.\d+\.\d+\.\d+$', c)]
            state = next((c for c in cols if c.lower() in ('master', 'backup', 'init')), '')
            if not ips:
                continue
            result['protocol'] = 'vrrp'
            result['vip'] = ips[-1]
            if len(ips) >= 2:
                result['active_ip'] = _resolve_local(ips[-2], secondary_lan_ip)
            result['secondary_is_active'] = state.lower() == 'master'
            return result

    return result


def parse_vrrp_vip(show_vrrp_brief, show_standby_brief=''):
    """Backward-compatible VIP-only accessor."""
    return parse_fhrp_state(show_vrrp_brief, show_standby_brief).get('vip', '')


def derive_primary_jump_targets(fhrp_state, secondary_lan_ip=''):
    """
    Return the SSH jump target for the secondary->primary login when the
    primary's management IP is down but the device is alive on the LAN.

    Per MOP: the jump uses the FHRP virtual IP (VRRP/HSRP VIP) only — never a
    physical interface IP. The VIP always resolves to whichever node is Active,
    which is the primary when only its management loopback is down.

    Returns a single-element list with the VIP, or [] if no VIP was parsed.
    """
    if not isinstance(fhrp_state, dict):
        return []
    vip = str(fhrp_state.get('vip', '')).strip()
    if not re.match(r'^\d+\.\d+\.\d+\.\d+$', vip):
        return []
    sec = str(secondary_lan_ip).strip()
    if vip == sec:
        return []
    return [vip]


class FilterModule(object):
    """Cisco Router Device Down Jinja2 filter plugin."""

    def filters(self):
        return {
            # JSON / parsing
            'safe_json_parse':                    safe_json_parse,
            'extract_ssh_output':                 extract_ssh_output,
            'parse_ping_result':                  parse_ping_result,
            # Platform
            'extract_platform':                   extract_platform,
            # Interface
            'parse_interface_state':              parse_interface_state,
            'parse_interface_ip_mask':            parse_interface_ip_mask,
            'parse_default_route_interface':      parse_default_route_interface,
            'parse_static_default_next_hop':      parse_static_default_next_hop,
            # WAN identification
            'derive_wan_interface_with_confidence': derive_wan_interface_with_confidence,
            'format_wan_identification_result':   format_wan_identification_result,
            # BGP
            'parse_bgp_vrf_map':                  parse_bgp_vrf_map,
            'parse_bgp_summary':                  parse_bgp_summary,
            'find_stuck_bgp_neighbors':           find_stuck_bgp_neighbors,
            'bgp_state_hint':                     bgp_state_hint,
            'build_bgp_clear_command':            build_bgp_clear_command,
            'build_bgp_vrf_summary_command':      build_bgp_vrf_summary_command,
            'get_bgp_discovery_commands':         get_bgp_discovery_commands,
            'merge_bgp_summary_outputs':          merge_bgp_summary_outputs,
            'build_bgp_underlay_commands':        build_bgp_underlay_commands,
            'build_bgp_neighbor_ping_cmd':        build_bgp_neighbor_ping_cmd,
            'evaluate_underlay_reachability':     evaluate_underlay_reachability,
            'corroborate_wan_pe_from_static':     corroborate_wan_pe_from_static,
            'parse_vrrp_vip':                     parse_vrrp_vip,
            'parse_fhrp_state':                   parse_fhrp_state,
            'derive_primary_jump_targets':        derive_primary_jump_targets,
            'parse_vty_acl':                      parse_vty_acl,
            'find_partner_candidates':            find_partner_candidates,
            'reject_non_router_devices':          reject_non_router_devices,
            'extract_bgp_update_source':          extract_bgp_update_source,
            'verify_bgp_neighbor_config':         verify_bgp_neighbor_config,
            'is_bgp_active':                      is_bgp_active,
            # PE derivation
            'derive_pe_ip':                       derive_pe_ip,
            'compute_other_end_ip':               compute_other_end_ip,
            # Input normalization
            'normalize_description':              normalize_description,
            'extract_neid_from_description':      extract_neid_from_description,
            'derive_shortname_from_neid':         derive_shortname_from_neid,
            'derive_site_group':                  derive_site_group,
            # VBSM sanitizer (v4+)
            'replace_update_with_notify':         replace_update_with_notify,
            # Config diff (v5)
            'diff_running_configs':               diff_running_configs,
            # Utility
            'summarize_phase_results':            summarize_phase_results,
            'extract_bgp_neighbor_section':       extract_bgp_neighbor_section,
            'check_privilege_denied':             check_privilege_denied,
            'precheck_aborted':                   precheck_aborted,
            'redact_password':                    redact_password,
        }
