"""
src/models/site_models.py

Typed data models for site configuration and UC execution context.
Using dataclasses for clean construction and testability.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SiteProfile:
    """
    Category-aware site profile resolved from region + metallic_type + design_type.
    Controls which use cases are enabled and what defaults to apply.
    """
    profile_id: str
    region: str
    metallic_type: str
    design_type: Optional[str]
    description: str
    enabled_use_cases: List[str]
    fw_transit_vlan_default: int = 50
    corporate_vpn: int = 30
    pepguest_vpn: int = 10
    pepinet_vpn: int = 20
    subif_delimiter: str = "."
    validation: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SiteConfig:
    """
    Full configuration for a single site, loaded from site_profiles.yaml.
    All fields map directly to vManage template variables or deployment parameters.
    """
    # ── Identity ─────────────────────────────────────────────
    site_name: str
    device_name: str
    system_ip: str
    device_uuid: str
    region: str
    metallic_type: str
    design_type: Optional[str] = None
    device_template_id: str = ""
    uc1_device_uuid: str = ""
    uc1_device_template_id: str = ""
    uc2_device_uuid: str = ""
    uc2_device_template_id: str = ""
    uc3_device_uuid: str = ""
    uc3_device_template_id: str = ""
    uc4_device_uuid: str = ""
    uc4_device_template_id: str = ""

    # ── UC1: Tracker Enable ───────────────────────────────────
    tracker_template_id: str = ""
    nat_template_id: str = ""
    nat_template_name: str = ""
    tracker_template_name: str = ""
    tracker_src_ip: str = ""

    # ── UC2: SIG Template ─────────────────────────────────────
    sig_template_id: str = ""
    cisco_sig_cred_template_id: str = ""
    sig_template_name: str = ""
    cisco_sig_cred_template_name: str = ""
    sig_variables: Dict[str, str] = field(default_factory=dict)

    # ── UC3: Create a Firewall Transit Interface ──────────────
    fw_physical_port: str = ""
    fw_transit_vlan: int = 50
    fw_transit_vpn: int = 0
    vpn0_noip_template_id: str = ""
    firewall_transit_template_id: str = ""
    vpn0_noip_template_name: str = ""
    firewall_transit_template_name: str = ""
    uc3_variables: Dict[str, str] = field(default_factory=dict)

    # ── UC4: Create a Firewall Transit Interface ──────────────
    pepguest_vpn_id: int = 10
    pepguest_vlan: int = 300
    pepguest_ip: str = ""
    pepguest_mask: str = ""
    pepguest_dhcp_helper: str = ""
    pepguest_vrrp_grpid: str = ""
    pepguest_vrrp_priority: str = ""
    pepguest_vrrp_vip: str = ""
    pepguest_vpn_template_id: str = ""
    pepguest_subif_template_id: str = ""
    pepinet_vpn_id: int = 20
    pepinet_vlan: int = 301
    pepinet_ip: str = ""
    pepinet_mask: str = ""
    pepinet_vpn_template_id: str = ""
    pepinet_subif_template_id: str = ""
    uc4_variables: Dict[str, str] = field(default_factory=dict)

    # ── Additional variables (passthrough) ────────────────────
    variables: Dict[str, str] = field(default_factory=dict)

    @property
    def fw_logical_port(self) -> str:
        """
        Derive the firewall transit logical (sub-interface) port from the
        physical port and VLAN. Example: GigabitEthernet0/0/1 → GigabitEthernet0/0/1.50
        """
        if self.fw_physical_port and self.fw_transit_vlan:
            return f"{self.fw_physical_port}.{self.fw_transit_vlan}"
        return ""

    def get_device_template_id(self, uc_key: str) -> str:
        specific = getattr(self, f"{uc_key}_device_template_id", "")
        return specific or self.device_template_id

    def get_device_uuid(self, uc_key: str) -> str:
        specific = getattr(self, f"{uc_key}_device_uuid", "")
        return specific or self.device_uuid

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SiteConfig":
        """Construct a SiteConfig from a raw YAML dict."""
        return cls(
            site_name=data.get("site_name", ""),
            device_name=data.get("device_name", ""),
            system_ip=data.get("system_ip", ""),
            device_uuid=data.get("device_uuid", ""),
            region=data.get("region", ""),
            metallic_type=data.get("metallic_type", ""),
            design_type=data.get("design_type"),
            device_template_id=data.get("device_template_id", ""),
            uc1_device_uuid=data.get("uc1_device_uuid", ""),
            uc1_device_template_id=data.get("uc1_device_template_id", ""),
            uc2_device_uuid=data.get("uc2_device_uuid", ""),
            uc2_device_template_id=data.get("uc2_device_template_id", ""),
            uc3_device_uuid=data.get("uc3_device_uuid", ""),
            uc3_device_template_id=data.get("uc3_device_template_id", ""),
            uc4_device_uuid=data.get("uc4_device_uuid", ""),
            uc4_device_template_id=data.get("uc4_device_template_id", ""),
            tracker_template_id=data.get("tracker_template_id", ""),
            nat_template_id=data.get("nat_template_id", ""),
            nat_template_name=data.get("nat_template_name", ""),
            tracker_template_name=data.get("tracker_template_name", ""),
            tracker_src_ip=data.get("tracker_src_ip", ""),
            sig_template_id=data.get("sig_template_id", ""),
            cisco_sig_cred_template_id=data.get("cisco_sig_cred_template_id", ""),
            sig_template_name=data.get("sig_template_name", ""),
            cisco_sig_cred_template_name=data.get("cisco_sig_cred_template_name", ""),
            sig_variables=data.get("sig_variables", {}),
            fw_physical_port=data.get("fw_physical_port", ""),
            fw_transit_vlan=data.get("fw_transit_vlan", 50),
            fw_transit_vpn=data.get("fw_transit_vpn", 0),
            vpn0_noip_template_id=data.get("vpn0_noip_template_id", ""),
            firewall_transit_template_id=data.get("firewall_transit_template_id", ""),
            vpn0_noip_template_name=data.get("vpn0_noip_template_name", ""),
            firewall_transit_template_name=data.get("firewall_transit_template_name", ""),
            uc3_variables=data.get("uc3_variables", {}),
            pepguest_vpn_id=data.get("pepguest_vpn_id", 10),
            pepguest_vlan=data.get("pepguest_vlan", 300),
            pepguest_ip=data.get("pepguest_ip", ""),
            pepguest_mask=data.get("pepguest_mask", ""),
            pepguest_dhcp_helper=data.get("pepguest_dhcp_helper", ""),
            pepguest_vrrp_grpid=data.get("pepguest_vrrp_grpid", ""),
            pepguest_vrrp_priority=data.get("pepguest_vrrp_priority", ""),
            pepguest_vrrp_vip=data.get("pepguest_vrrp_vip", ""),
            pepguest_vpn_template_id=data.get("pepguest_vpn_template_id", ""),
            pepguest_subif_template_id=data.get("pepguest_subif_template_id", ""),
            pepinet_vpn_id=data.get("pepinet_vpn_id", 20),
            pepinet_vlan=data.get("pepinet_vlan", 301),
            pepinet_ip=data.get("pepinet_ip", ""),
            pepinet_mask=data.get("pepinet_mask", ""),
            pepinet_vpn_template_id=data.get("pepinet_vpn_template_id", ""),
            pepinet_subif_template_id=data.get("pepinet_subif_template_id", ""),
            uc4_variables=data.get("uc4_variables", {}),
            variables=data.get("variables", {}),
        )
