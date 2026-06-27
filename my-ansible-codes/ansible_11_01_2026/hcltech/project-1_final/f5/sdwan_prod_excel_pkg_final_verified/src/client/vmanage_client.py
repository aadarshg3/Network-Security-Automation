"""
src/client/vmanage_client.py

Production-quality vManage REST API client.
- Session management with CSRF token handling
- Configurable retry with exponential backoff
- Explicit error handling with typed exceptions
- Poll-to-completion for async deploy tasks
- Soft error detection: "config diff generation" treated as warning, not failure
- Mock-friendly: all API calls go through _get / _post / _put — easy to stub in tests
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple
import urllib3

import requests
from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import Timeout as RequestsTimeout
from urllib3.util.retry import Retry

from src.client.exceptions import (
    VManageAPIError,
    VManageAuthError,
    VManageTimeoutError,
    DeploymentError,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("sdwan.client")

# Patterns that indicate a soft error (config landed but diff readback failed)
SOFT_ERROR_PATTERNS: List[str] = [
    "error in generating configuration diff",
    "error generating configuration diff",
    "generating configuration diff",
    "config diff",
]


class VManageClient:
    """
    Reusable vManage REST client.

    Usage:
        client = VManageClient(host="https://192.168.1.1", verify_ssl=False)
        client.login("admin", "password")
        template = client.get_device_template("template-uuid")
    """

    def __init__(
        self,
        host: str,
        verify_ssl: bool = False,
        timeout: int = 30,
        retry_attempts: int = 3,
        retry_delay: float = 5.0,
        poll_timeout: int = 180,
        poll_interval: int = 5,
        soft_error_patterns: Optional[List[str]] = None,
    ):
        self.host = host.rstrip("/")
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.poll_timeout = poll_timeout
        self.poll_interval = poll_interval
        self.soft_error_patterns = soft_error_patterns or SOFT_ERROR_PATTERNS
        self._session: Optional[Session] = None

    # ──────────────────────────────────────────────────────────────────────
    # Authentication
    # ──────────────────────────────────────────────────────────────────────

    def login(self, username: str, password: str) -> None:
        """Authenticate and obtain a session with CSRF token."""
        self._session = self._build_session()
        url = f"{self.host}/j_security_check"
        logger.info(f"Logging in to vManage at {self.host} as '{username}'")
        resp = self._login_request(url, username, password)
        if resp.status_code == 401:
            raise VManageAuthError(
                f"Login failed for user '{username}' at {self.host} "
                f"(status={resp.status_code}, url={resp.url}, "
                f"content_type={resp.headers.get('Content-Type', '')})"
            )

        # Some vManage builds return HTTP 200 with an empty body and keep the final
        # URL at /j_security_check even on success, so rely on token retrieval rather
        # than the post-login URL alone.
        token = self._fetch_csrf_token()
        if not token:
            raise VManageAuthError(
                f"Login failed for user '{username}' at {self.host} "
                f"(status={resp.status_code}, url={resp.url}, "
                f"content_type={resp.headers.get('Content-Type', '')})"
            )
        logger.info("Login successful")

    def _fetch_csrf_token(self) -> str:
        """Fetch and store the CSRF token required for write operations."""
        url = f"{self.host}/dataservice/client/token"
        resp = self._token_request(url)
        content_type = resp.headers.get("Content-Type", "")
        body = resp.text.strip()
        if (
            resp.status_code == 200
            and body
            and "html" not in content_type.lower()
            and "<html" not in body.lower()
        ):
            token = body
            self._session.headers.update({"X-XSRF-TOKEN": token})
            logger.debug("CSRF token obtained")
            return token
        return ""

    def _login_request(self, url: str, username: str, password: str, attempt: int = 1):
        try:
            return self._session.post(
                url,
                data={"j_username": username, "j_password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                verify=self.verify_ssl,
                timeout=self.timeout,
                allow_redirects=True,
            )
        except (RequestsTimeout, RequestsConnectionError) as exc:
            if attempt <= self.retry_attempts:
                logger.warning(
                    "Login request failed (%s) - retry %s/%s",
                    exc.__class__.__name__,
                    attempt,
                    self.retry_attempts,
                )
                time.sleep(self.retry_delay * attempt)
                return self._login_request(url, username, password, attempt + 1)
            raise VManageTimeoutError(
                f"Login to {self.host} failed after {self.retry_attempts} retries: {exc}"
            ) from exc

    def _token_request(self, url: str, attempt: int = 1):
        try:
            return self._session.get(url, verify=self.verify_ssl, timeout=self.timeout)
        except (RequestsTimeout, RequestsConnectionError) as exc:
            if attempt <= self.retry_attempts:
                logger.warning(
                    "Token fetch failed (%s) - retry %s/%s",
                    exc.__class__.__name__,
                    attempt,
                    self.retry_attempts,
                )
                time.sleep(self.retry_delay * attempt)
                return self._token_request(url, attempt + 1)
            raise VManageTimeoutError(
                f"Token fetch from {self.host} failed after {self.retry_attempts} retries: {exc}"
            ) from exc

    def logout(self) -> None:
        """Gracefully close the vManage session."""
        if self._session:
            try:
                self._session.get(
                    f"{self.host}/logout",
                    verify=self.verify_ssl,
                    timeout=self.timeout,
                )
            except Exception:
                pass
            finally:
                self._session.close()
                self._session = None
            logger.info("Logged out of vManage")

    # ──────────────────────────────────────────────────────────────────────
    # Device Template Operations
    # ──────────────────────────────────────────────────────────────────────

    def list_device_templates(self) -> List[Dict[str, Any]]:
        """Return all device templates."""
        return self._get("/dataservice/template/device")["data"]

    def get_device_template(self, template_id: str) -> Dict[str, Any]:
        """Fetch the full JSON definition of a device template."""
        data = self._get(f"/dataservice/template/device/object/{template_id}")
        logger.debug(f"Fetched device template: {template_id[:8]}...")
        return data

    def update_device_template(self, template_id: str, template_data: Dict[str, Any]) -> None:
        """Update (PUT) a device template with modified data."""
        self._put(f"/dataservice/template/device/{template_id}", json=template_data)
        logger.info(f"Device template updated: {template_id[:8]}...")

    def rollback_device_template(self, template_id: str, backup_data: Dict[str, Any]) -> None:
        """Restore a device template from a backup snapshot (PUT)."""
        logger.warning(f"Rolling back device template: {template_id[:8]}...")
        self._put(f"/dataservice/template/device/{template_id}", json=backup_data)
        logger.info(f"Rollback PUT complete for template: {template_id[:8]}...")

    # ──────────────────────────────────────────────────────────────────────
    # Feature Template Operations
    # ──────────────────────────────────────────────────────────────────────

    def list_feature_templates(self, filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List feature templates, optionally filtered by templateType."""
        data = self._get("/dataservice/template/feature")["data"]
        if filter_type:
            data = [t for t in data if t.get("templateType") == filter_type]
        return data

    def get_feature_template(self, template_id: str) -> Dict[str, Any]:
        """Fetch full JSON of a feature template."""
        return self._get(f"/dataservice/template/feature/object/{template_id}")

    # ──────────────────────────────────────────────────────────────────────
    # Variable Inputs & Deploy
    # ──────────────────────────────────────────────────────────────────────

    def get_inputs(
        self, template_id: str, device_uuid: str
    ) -> List[Dict[str, Any]]:
        """
        Fetch the list of variable input slots for a device template + device.
        POST /dataservice/template/device/config/input
        """
        payload = {
            "templateId": template_id,
            "deviceIds": [device_uuid],
            "isEdited": "false",
            "isMasterEdited": "false",
        }
        resp = self._post("/dataservice/template/device/config/input", json=payload)
        return resp.get("data", [])

    def attach_and_deploy(
        self,
        template_id: str,
        inputs: List[Dict[str, Any]],
        is_edited: bool = True,
    ) -> str:
        """
        Attach template with variables and trigger deploy.
        Returns the action_id for polling.
        POST /dataservice/template/device/config/attachfeature
        """
        payload = {
            "deviceTemplateList": [
                {
                    "templateId": template_id,
                    "device": inputs,
                    "isEdited": is_edited,
                    "isMasterEdited": False,
                }
            ]
        }
        resp = self._post("/dataservice/template/device/config/attachfeature", json=payload)
        action_id = resp.get("id", "")
        if not action_id:
            raise DeploymentError(
                "attachfeature returned no action ID", template_id
            )
        logger.info(f"Deploy triggered — action_id: {action_id}")
        return action_id

    def get_config_preview(
        self, template_id: str, variables: Dict[str, Any]
    ) -> str:
        """Fetch rendered device config preview for diff generation."""
        payload = {
            "templateId": template_id,
            "device": variables,
            "isEdited": True,
        }
        try:
            resp = self._post(
                "/dataservice/template/device/config/config", json=payload
            )
            return resp.get("config", "")
        except VManageAPIError as exc:
            if exc.status_code == 406:
                logger.info("Config preview not available from vManage; continuing without diff readback")
                return ""
            logger.warning(f"Config preview fetch failed (non-fatal): {exc}")
            return ""
        except Exception as exc:
            logger.warning(f"Config preview fetch failed (non-fatal): {exc}")
            return ""

    # ──────────────────────────────────────────────────────────────────────
    # Poll / Task Tracking
    # ──────────────────────────────────────────────────────────────────────

    def poll_task(self, action_id: str) -> Dict[str, Any]:
        """
        Poll vManage for task completion with soft error support.

        Returns a result dict:
          status:   "success" | "failure" | "timeout"
          soft:     True if a config-diff-generation warning was detected
          soft_msg: list of warning strings
          success:  count of successful devices
          failure:  count of failed devices
          data:     raw task data entries
        """
        url = f"/dataservice/device/action/status/{action_id}"
        deadline = time.time() + self.poll_timeout
        logger.info(f"Polling action {action_id} (timeout={self.poll_timeout}s)")

        while time.time() < deadline:
            try:
                resp = self._get(url)
            except VManageAPIError as exc:
                logger.warning(f"Poll request failed (retrying): {exc}")
                time.sleep(self.poll_interval)
                continue

            summary = resp.get("summary", {})
            status  = summary.get("status", "").lower()
            success = int(summary.get("count", {}).get("Done", 0))
            failure = int(summary.get("count", {}).get("Schedule", 0)) + \
                      int(summary.get("count", {}).get("Failure", 0))
            data    = resp.get("data", [])

            if status in ("done", "success"):
                soft, soft_msgs = self._detect_soft_errors(data)
                if soft:
                    logger.info(
                        f"Action {action_id} completed; vManage diff readback was unavailable"
                    )
                    return {
                        "status":    "success",
                        "soft":      True,
                        "soft_msg":  soft_msgs,
                        "success":   success + failure,  # treat all as success
                        "failure":   0,
                        "data":      data,
                    }
                if failure > 0:
                    logger.error(f"Action {action_id} failed on {failure} device(s)")
                    return {
                        "status":   "failure",
                        "soft":     False,
                        "soft_msg": [],
                        "success":  success,
                        "failure":  failure,
                        "data":     data,
                    }
                logger.info(f"Action {action_id} succeeded on {success} device(s)")
                return {
                    "status":   "success",
                    "soft":     False,
                    "soft_msg": [],
                    "success":  success,
                    "failure":  0,
                    "data":     data,
                }

            logger.debug(f"  Task status: {status} — waiting {self.poll_interval}s")
            time.sleep(self.poll_interval)

        logger.error(f"Action {action_id} timed out after {self.poll_timeout}s")
        return {
            "status":   "timeout",
            "soft":     False,
            "soft_msg": [],
            "success":  0,
            "failure":  0,
            "data":     [],
        }

    # ──────────────────────────────────────────────────────────────────────
    # Device Listing
    # ──────────────────────────────────────────────────────────────────────

    def list_devices(self) -> List[Dict[str, Any]]:
        """List all vManage-managed devices."""
        return self._get("/dataservice/device")["data"]

    # ──────────────────────────────────────────────────────────────────────
    # Internal HTTP Helpers
    # ──────────────────────────────────────────────────────────────────────

    def _get(self, path: str) -> Dict[str, Any]:
        return self._request("GET", path)

    def _post(self, path: str, json: Dict[str, Any] = None) -> Dict[str, Any]:
        return self._request("POST", path, json=json)

    def _put(self, path: str, json: Dict[str, Any] = None) -> Dict[str, Any]:
        return self._request("PUT", path, json=json)

    def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        attempt: int = 1,
    ) -> Dict[str, Any]:
        if self._session is None:
            raise VManageAuthError("Not logged in — call client.login() first")

        url = f"{self.host}{path}"
        try:
            resp = self._session.request(
                method,
                url,
                json=json,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
        except RequestsTimeout:
            if attempt <= self.retry_attempts:
                logger.warning(f"Timeout on {method} {path} — retry {attempt}/{self.retry_attempts}")
                time.sleep(self.retry_delay * attempt)
                return self._request(method, path, json=json, attempt=attempt + 1)
            raise VManageTimeoutError(f"Timed out after {self.retry_attempts} attempts: {url}")
        except RequestsConnectionError as exc:
            if attempt <= self.retry_attempts:
                logger.warning(f"Connection error on {method} {path} — retry {attempt}/{self.retry_attempts}")
                time.sleep(self.retry_delay * attempt)
                return self._request(method, path, json=json, attempt=attempt + 1)
            raise VManageAPIError(str(exc), url=url)

        if resp.status_code == 401:
            raise VManageAuthError(f"Session expired or unauthorized: {url}")
        if resp.status_code >= 400:
            raise VManageAPIError(
                f"{method} {path} returned {resp.status_code}: {resp.text[:200]}",
                status_code=resp.status_code,
                url=url,
            )

        try:
            return resp.json() if resp.text.strip() else {}
        except ValueError:
            return {"raw": resp.text}

    def _build_session(self) -> Session:
        session = Session()
        session.headers.update({
            "Accept":       "application/json",
        })
        adapter = HTTPAdapter(
            max_retries=Retry(
                total=0,  # we handle retries ourselves
                raise_on_status=False,
            )
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _detect_soft_errors(
        self, data: List[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """
        Detect soft errors in task data entries.
        A soft error is a failure that is actually a config-diff-generation
        warning — the config DID reach the device, only the diff readback failed.
        """
        soft_msgs: List[str] = []
        for entry in data:
            activity = entry.get("currentActivity", "") or ""
            for line in entry.get("activity", []):
                activity += " " + line
            for pattern in self.soft_error_patterns:
                if pattern.lower() in activity.lower():
                    soft_msgs.append(activity.strip()[:200])
                    break
        return bool(soft_msgs), soft_msgs
