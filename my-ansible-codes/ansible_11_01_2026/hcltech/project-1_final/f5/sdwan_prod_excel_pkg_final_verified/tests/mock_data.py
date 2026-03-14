"""
tests/mock_data.py

Shared mock data, fixtures, and stub factories for unit tests.
All tests run without a live vManage — mock the client transport layer only.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

from src.models.site_models import SiteConfig, SiteProfile


# ── Sample site configs ────────────────────────────────────────────────────

def make_site(overrides: Dict[str, Any] = None) -> SiteConfig:
    """Return a fully populated SiteConfig for testing."""
    defaults = dict(
        site_name="test-site1",
        device_name="cedge-test-01",
        system_ip="1.1.1.10",
        device_uuid="C8K-AABBCCDD-1234-5678-ABCD-0011223344FF",
        region="APAC",
        metallic_type="Gold",
        design_type=None,
        device_template_id="aaaa-1111-bbbb-2222-cccc3333dddd",
        # UC1
        tracker_template_id="tracker-tid-001",
        nat_template_id="nat-tid-001",
        tracker_template_name="cisco-tracker-template",
        nat_template_name="cisco-nat-template",
        tracker_src_ip="10.2.3.7/32",
        # UC2
        sig_template_id="sig-tid-001",
        cisco_sig_cred_template_id="sig-cred-tid-001",
        sig_template_name="cisco-sig-template",
        cisco_sig_cred_template_name="cisco-sig-cred-template",
        sig_variables={
            "/0/0/vpn-instance/interface/gre205/description": "Zscaler_primary_DC",
            "/0/0/vpn-instance/tracker-src-ip": "115.113.186.186/32",
        },
        # UC3
        fw_physical_port="GigabitEthernet0/0/1",
        fw_transit_vlan=50,
        fw_transit_vpn=0,
        vpn0_noip_template_id="noip-tid-001",
        firewall_transit_template_id="fw-transit-tid-001",
        vpn0_noip_template_name="fw-transit-noip-template",
        firewall_transit_template_name="fw-transit-subif-template",
        uc3_variables={
            "/0/VPN0_INT_Zscaler_interface_NAME/interface/if-name": "GigabitEthernet0/0/1",
            "/0/VPN0_INT_Zscaler_interface_NAME/interface/description": "FW Transit",
            "/0/VPN0_INT_Zscaler_interface_NAME/interface/mtu": "1504",
            "/3/INT03_NO-DHCP-HELPER_interface_NAME/interface/if-name": "GigabitEthernet0/0/1.50",
        },
        # UC4
        pepguest_vpn_id=10,
        pepguest_vlan=300,
        pepguest_ip="11.161.161.130",
        pepguest_mask="255.255.255.192",
        pepguest_dhcp_helper="30.159.73.58",
        pepguest_vrrp_grpid="5",
        pepguest_vrrp_priority="120",
        pepguest_vrrp_vip="11.161.161.129",
        pepguest_vpn_template_id="pepguest-vpn-aaaa-1111",
        pepguest_subif_template_id="pepguest-subif-bbbb-2222",
        pepinet_vpn_id=20,
        pepinet_vlan=301,
        pepinet_ip="11.163.161.130",
        pepinet_mask="255.255.255.192",
        pepinet_vpn_template_id="pepinet-vpn-cccc-3333",
        pepinet_subif_template_id="pepinet-subif-dddd-4444",
        uc4_variables={
            "[PEPguest_VPN_5_subintf_name]":  "GigabitEthernet0/0/1.300",
            "[PEPguest_if_ipv4_address]":     "11.161.161.130/26",
            "[PEPguest_if_dhcp_helper]":      "30.159.73.58",
            "[PEPguest_if_vrrp_grpid]":       "5",
            "[PEPguest_if_vrrp_priority]":    "120",
            "[PEPguest_if_vrrp_vip]":         "11.161.161.129",
            "[PEPguest_VPN_12_subintf_name]": "GigabitEthernet0/0/1.301",
        },
        variables={},
    )
    if overrides:
        defaults.update(overrides)
    return SiteConfig.from_dict(defaults)


def make_profile(overrides: Dict[str, Any] = None) -> SiteProfile:
    defaults = dict(
        profile_id="apac_gold",
        region="APAC",
        metallic_type="Gold",
        design_type=None,
        description="Test APAC Gold profile",
        enabled_use_cases=["uc1", "uc2", "uc3", "uc4"],
        fw_transit_vlan_default=50,
        corporate_vpn=30,
        pepguest_vpn=10,
        pepinet_vpn=20,
        validation={"check_duplicate_variables": True, "vlan_min": 1, "vlan_max": 4094},
    )
    if overrides:
        defaults.update(overrides)
    return SiteProfile(**defaults)


# ── Mock device template ────────────────────────────────────────────────────

def make_device_template(extra_subtemplates: List[Dict] = None) -> Dict[str, Any]:
    return {
        "templateId":   "aaaa-1111-bbbb-2222-cccc3333dddd",
        "templateName": "Test-Device-Template",
        "templateType": "device",
        "deviceType":   "vedge-C8000V",
        "generalTemplates": [
            {
                "templateId":   "vpn0-transport-template-id",
                "templateType": "cisco_vpn",
                "subTemplates": extra_subtemplates or [],
            },
            {
                "templateId":   "vpn512-mgmt-template-id",
                "templateType": "cisco_vpn",
                "subTemplates": [],
            },
        ],
    }


def make_feature_templates(names_and_types: List[tuple]) -> List[Dict[str, Any]]:
    """Build a list of feature template dicts from (name, type, id) tuples."""
    return [
        {
            "templateId":   tid,
            "templateName": name,
            "templateType": ttype,
        }
        for name, ttype, tid in names_and_types
    ]


# ── Poll results ───────────────────────────────────────────────────────────

def poll_success() -> Dict[str, Any]:
    return {"status": "success", "soft": False, "soft_msg": [], "success": 1, "failure": 0, "data": []}

def poll_soft_error() -> Dict[str, Any]:
    return {
        "status": "success", "soft": True,
        "soft_msg": ["Error in generating configuration diff"],
        "success": 1, "failure": 0, "data": [],
    }

def poll_failure() -> Dict[str, Any]:
    return {
        "status": "success", "soft": False, "soft_msg": [],
        "success": 0, "failure": 1,
        "data": [{"statusId": "failure", "host-name": "cedge-01",
                  "currentActivity": "Template push failed", "activity": []}],
    }

def poll_timeout() -> Dict[str, Any]:
    return {"status": "timeout", "soft": False, "soft_msg": [], "success": 0, "failure": 0, "data": []}


# ── Mock client factory ────────────────────────────────────────────────────

def make_mock_client(
    template: Dict = None,
    feature_templates: List[Dict] = None,
    poll_result: Dict = None,
    inputs: List[Dict] = None,
) -> MagicMock:
    """Create a fully pre-configured mock VManageClient."""
    client = MagicMock()
    client.get_device_template.return_value   = template or make_device_template()
    client.list_feature_templates.return_value = feature_templates or []
    client.get_inputs.return_value            = inputs or [{"csv-status": "completed", "csv-deviceId": "C8K-test"}]
    client.attach_and_deploy.return_value     = "mock-action-id-001"
    client.poll_task.return_value             = poll_result or poll_success()
    client.get_config_preview.return_value    = "interface GigabitEthernet0/0/1\n no ip address\n"
    client.update_device_template.return_value = {}
    client.rollback_device_template.return_value = {}
    client.get_feature_template.side_effect = lambda template_id: {
        "templateId": template_id,
        "templateDefinition": {
            "vpn-id": {
                "vipValue": 0 if template_id == "vpn0-transport-template-id" else 512
            }
        },
    }
    return client
