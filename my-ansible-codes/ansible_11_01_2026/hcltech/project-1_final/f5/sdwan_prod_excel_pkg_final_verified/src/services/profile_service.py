"""
src/services/profile_service.py

Category-aware site profile resolution.

The customer stated:
  "we have multiple categories based on region and metallic type,
   and therefore the use cases will vary depending on the category of the site"

Resolution order (most specific → least specific):
  1. region + metallic_type + design_type
  2. region + metallic_type
  3. region only
  4. default
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from src.models.site_models import SiteProfile
from src.client.exceptions import ProfileNotFoundError

logger = logging.getLogger("sdwan.profile")


class ProfileService:
    """Resolves site profiles from YAML config based on region/metallic/design."""

    def __init__(self, profiles_config: Dict[str, Any]):
        self._raw_profiles: List[Dict[str, Any]] = profiles_config.get("profiles", [])
        self._default_cfg:  Dict[str, Any] = profiles_config.get("default", {})
        self._profiles: List[SiteProfile]  = self._build_profiles()

    def resolve(
        self,
        region: str,
        metallic_type: str,
        design_type: Optional[str] = None,
    ) -> SiteProfile:
        """
        Resolve the most specific matching profile.
        Falls back to default if no profile matches.
        """
        region_n  = (region or "").strip().upper()
        metallic_n = (metallic_type or "").strip()
        design_n   = (design_type or "").strip() or None

        # Pass 1: exact match including design_type
        if design_n:
            for p in self._profiles:
                if (
                    p.region.upper() == region_n
                    and p.metallic_type == metallic_n
                    and p.design_type == design_n
                ):
                    logger.info(
                        f"Profile resolved: {p.profile_id} "
                        f"(region={region} metallic={metallic_type} design={design_type})"
                    )
                    return p

        # Pass 2: region + metallic (no design_type constraint)
        for p in self._profiles:
            if (
                p.region.upper() == region_n
                and p.metallic_type == metallic_n
                and p.design_type is None
            ):
                logger.info(
                    f"Profile resolved: {p.profile_id} "
                    f"(region={region} metallic={metallic_type})"
                )
                return p

        # Pass 3: fallback to default
        logger.warning(
            f"No profile found for region='{region}' metallic='{metallic_type}' "
            f"design='{design_type}' — using default profile"
        )
        return self._build_default()

    def list_profiles(self) -> List[SiteProfile]:
        return list(self._profiles)

    # ──────────────────────────────────────────────────────────────────────
    # Internal
    # ──────────────────────────────────────────────────────────────────────

    def _build_profiles(self) -> List[SiteProfile]:
        profiles = []
        for raw in self._raw_profiles:
            profiles.append(SiteProfile(
                profile_id=raw.get("id", "unknown"),
                region=raw.get("region", ""),
                metallic_type=raw.get("metallic_type", ""),
                design_type=raw.get("design_type"),
                description=raw.get("description", ""),
                enabled_use_cases=raw.get("enabled_use_cases", ["uc1", "uc2", "uc3", "uc4"]),
                fw_transit_vlan_default=raw.get("fw_transit_vlan_default", 50),
                corporate_vpn=raw.get("corporate_vpn", 30),
                pepguest_vpn=raw.get("pepguest_vpn", 10),
                pepinet_vpn=raw.get("pepinet_vpn", 20),
                validation=raw.get("validation", {}),
            ))
        return profiles

    def _build_default(self) -> SiteProfile:
        d = self._default_cfg
        return SiteProfile(
            profile_id="default",
            region="*",
            metallic_type="*",
            design_type=None,
            description=d.get("description", "Default fallback profile"),
            enabled_use_cases=d.get("enabled_use_cases", ["uc1", "uc2", "uc3", "uc4"]),
            fw_transit_vlan_default=d.get("fw_transit_vlan_default", 50),
            corporate_vpn=d.get("corporate_vpn", 30),
            pepguest_vpn=d.get("pepguest_vpn", 10),
            pepinet_vpn=d.get("pepinet_vpn", 20),
            validation=d.get("validation", {}),
        )
