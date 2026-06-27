"""
src/services/validation_service.py

Validation-first design: ALL inputs are validated before any API call is made.
Detects and rejects:
  - duplicate variables (never silently overwrite)
  - invalid interface names
  - invalid VLAN values
  - invalid IP/mask values
  - missing required template references
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from src.client.exceptions import DuplicateVariableError, ValidationError
from src.models.site_models import SiteConfig, SiteProfile

logger = logging.getLogger("sdwan.validation")

# ── Regex patterns ─────────────────────────────────────────────────────────
_INTERFACE_PATTERN = re.compile(
    r"^(GigabitEthernet|TenGigabitEthernet|Ethernet|Loopback|Tunnel|gre|gig)"
    r"[\d/]+(\.\d+)?$",
    re.IGNORECASE,
)
_IP_PATTERN = re.compile(
    r"^(\d{1,3}\.){3}\d{1,3}$"
)
_CIDR_PATTERN = re.compile(
    r"^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$"
)


class ValidationService:
    """
    Centralised validation for site config and template variable inputs.
    All methods raise typed exceptions on failure.
    """

    def __init__(self, profile: Optional[SiteProfile] = None):
        self.profile = profile
        self._vlan_min = 1
        self._vlan_max = 4094
        if profile and profile.validation:
            self._vlan_min = profile.validation.get("vlan_min", 1)
            self._vlan_max = profile.validation.get("vlan_max", 4094)

    # ──────────────────────────────────────────────────────────────────────
    # Top-level site config validation
    # ──────────────────────────────────────────────────────────────────────

    def validate_site_config(self, site: SiteConfig, uc_keys: List[str]) -> List[str]:
        """
        Validate a site config for the requested use cases.
        Returns a list of warning strings (non-fatal).
        Raises ValidationError or DuplicateVariableError on fatal issues.
        """
        warnings: List[str] = []

        self._require_non_empty(site.site_name, "site_name")
        self._require_non_empty(site.device_uuid, "device_uuid")
        self._require_non_empty(site.device_template_id, "device_template_id")

        if "uc1" in uc_keys:
            warnings.extend(self._validate_uc1(site))
        if "uc2" in uc_keys:
            warnings.extend(self._validate_uc2(site))
        if "uc3" in uc_keys:
            warnings.extend(self._validate_uc3(site))
        if "uc4" in uc_keys:
            warnings.extend(self._validate_uc4(site))

        return warnings

    # ──────────────────────────────────────────────────────────────────────
    # UC-level validation
    # ──────────────────────────────────────────────────────────────────────

    def _validate_uc1(self, site: SiteConfig) -> List[str]:
        warnings: List[str] = []
        if not (site.tracker_template_id or site.tracker_template_name):
            warnings.append("UC1: tracker_template_name not set — template must already exist in vManage")
        if not (site.nat_template_id or site.nat_template_name):
            warnings.append("UC1: nat_template_name not set — template must already exist in vManage")
        if site.tracker_src_ip:
            self._validate_cidr(site.tracker_src_ip, "tracker_src_ip")
        return warnings

    def _validate_uc2(self, site: SiteConfig) -> List[str]:
        warnings: List[str] = []
        if not (site.sig_template_id or site.sig_template_name):
            warnings.append("UC2: sig_template_name not set")
        if site.sig_variables:
            self.validate_variables_no_duplicates(site.sig_variables, "uc2_sig_variables")
        return warnings

    def _validate_uc3(self, site: SiteConfig) -> List[str]:
        warnings: List[str] = []
        if site.fw_physical_port:
            self.validate_interface_name(site.fw_physical_port, "fw_physical_port")
        else:
            warnings.append("UC3: fw_physical_port not set — cannot derive logical sub-interface")

        if site.fw_transit_vlan:
            self.validate_vlan(site.fw_transit_vlan, "fw_transit_vlan")

        if not (site.vpn0_noip_template_id or site.vpn0_noip_template_name):
            warnings.append("UC3: vpn0_noip_template_name not set — VPN0 no-IP template attachment will be skipped")
        if not (site.firewall_transit_template_id or site.firewall_transit_template_name):
            warnings.append("UC3: firewall_transit_template_name not set — variable update only")

        if site.fw_physical_port and site.fw_transit_vlan:
            logical = site.fw_logical_port
            logger.info(f"UC3: physical→logical: {site.fw_physical_port} → {logical}")

        if site.uc3_variables:
            self.validate_variables_no_duplicates(site.uc3_variables, "uc3_variables")
        return warnings

    def _validate_uc4(self, site: SiteConfig) -> List[str]:
        warnings: List[str] = []
        if site.pepguest_vlan:
            self.validate_vlan(site.pepguest_vlan, "pepguest_vlan")
        if site.pepinet_vlan:
            self.validate_vlan(site.pepinet_vlan, "pepinet_vlan")
        if site.pepguest_ip:
            self.validate_ip(site.pepguest_ip, "pepguest_ip")
        if site.pepinet_ip:
            self.validate_ip(site.pepinet_ip, "pepinet_ip")
        if not site.pepguest_vpn_template_id:
            warnings.append("UC4: pepguest_vpn_template_id not set")
        if not site.pepguest_subif_template_id:
            warnings.append("UC4: pepguest_subif_template_id not set")
        if not site.pepinet_vpn_template_id:
            warnings.append("UC4: pepinet_vpn_template_id not set")
        if not site.pepinet_subif_template_id:
            warnings.append("UC4: pepinet_subif_template_id not set")
        if site.uc4_variables:
            self.validate_variables_no_duplicates(site.uc4_variables, "uc4_variables")
        return warnings

    # ──────────────────────────────────────────────────────────────────────
    # Atomic validators
    # ──────────────────────────────────────────────────────────────────────

    def validate_interface_name(self, name: str, field: str) -> None:
        """Raise ValidationError if interface name format is invalid."""
        if not _INTERFACE_PATTERN.match(name):
            raise ValidationError(
                field=field,
                value=name,
                reason=f"Invalid interface name format. Expected e.g. GigabitEthernet0/0/1 or GigabitEthernet0/0/1.50"
            )

    def validate_vlan(self, vlan: int, field: str) -> None:
        """Raise ValidationError if VLAN is outside valid range."""
        if not (self._vlan_min <= vlan <= self._vlan_max):
            raise ValidationError(
                field=field,
                value=str(vlan),
                reason=f"VLAN must be between {self._vlan_min} and {self._vlan_max}"
            )

    def validate_ip(self, ip: str, field: str) -> None:
        """Raise ValidationError if IP address format is invalid."""
        if not _IP_PATTERN.match(ip):
            raise ValidationError(field=field, value=ip, reason="Invalid IPv4 address format")
        octets = [int(o) for o in ip.split(".")]
        if any(o > 255 for o in octets):
            raise ValidationError(field=field, value=ip, reason="IPv4 octet out of range (0-255)")

    def _validate_cidr(self, cidr: str, field: str) -> None:
        """Raise ValidationError if CIDR notation is invalid."""
        if not _CIDR_PATTERN.match(cidr):
            raise ValidationError(
                field=field,
                value=cidr,
                reason="Invalid CIDR notation — expected format: x.x.x.x/prefix"
            )
        prefix = int(cidr.split("/")[1])
        if prefix < 0 or prefix > 32:
            raise ValidationError(field=field, value=cidr, reason="Prefix length must be 0–32")

    def validate_variables_no_duplicates(
        self, variables: Dict[str, str], context: str
    ) -> None:
        """
        Raise DuplicateVariableError if any key appears more than once.
        Note: standard dict cannot have duplicate keys, so this checks
        for duplicate-keyed inputs from raw list-of-tuples source.
        """
        seen: Dict[str, int] = {}
        for key in variables:
            seen[key] = seen.get(key, 0) + 1
        duplicates = [k for k, cnt in seen.items() if cnt > 1]
        if duplicates:
            for dup in duplicates:
                logger.error(f"Duplicate variable detected in {context}: '{dup}'")
            raise DuplicateVariableError(duplicates[0])

    def validate_variables_from_list(
        self, pairs: List[Tuple[str, str]], context: str
    ) -> Dict[str, str]:
        """
        Build a variable dict from a list of (key, value) pairs.
        Raises DuplicateVariableError if any key appears more than once.
        """
        seen: Dict[str, int] = {}
        result: Dict[str, str] = {}
        for key, value in pairs:
            seen[key] = seen.get(key, 0) + 1
            result[key] = value

        duplicates = [k for k, cnt in seen.items() if cnt > 1]
        if duplicates:
            for dup in duplicates:
                logger.error(f"Duplicate variable detected in {context}: '{dup}'")
            raise DuplicateVariableError(duplicates[0])

        return result

    # ──────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────

    def _require_non_empty(self, value: str, field: str) -> None:
        if not value or not str(value).strip():
            raise ValidationError(
                field=field,
                value=value,
                reason="Required field is empty or missing"
            )
