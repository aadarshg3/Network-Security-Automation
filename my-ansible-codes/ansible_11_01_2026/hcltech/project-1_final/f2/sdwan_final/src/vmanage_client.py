import json
import logging
import time

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger("sdwan.client")


class VManageClient:
    def __init__(self, host):
        self.host    = host.rstrip("/")
        self.session = requests.Session()

    def login(self, username, password):
        r = self.session.post(
            f"{self.host}/j_security_check",
            data={"j_username": username, "j_password": password},
            verify=False
        )
        if r.status_code != 200 or "html" in r.text.lower():
            raise Exception(f"Login failed HTTP {r.status_code}")
        t = self.session.get(f"{self.host}/dataservice/client/token", verify=False)
        if t.status_code != 200:
            raise Exception("Failed to fetch CSRF token")
        self.session.headers["X-XSRF-TOKEN"] = t.text
        logger.info("Login OK")

    def get_device_template(self, template_id):
        r = self.session.get(
            f"{self.host}/dataservice/template/device/object/{template_id}",
            verify=False
        )
        if r.status_code != 200:
            raise Exception(f"GET device template failed: {r.text}")
        return r.json()

    def update_device_template(self, template_id, payload):
        r = self.session.put(
            f"{self.host}/dataservice/template/device/{template_id}",
            json=payload,
            verify=False
        )
        if r.status_code != 200:
            raise Exception(f"PUT device template failed: {r.text}")
        logger.info(f"Template updated: {template_id[:8]}...")

    def rollback_device_template(self, template_id, backup_data):
        r = self.session.put(
            f"{self.host}/dataservice/template/device/{template_id}",
            json=backup_data,
            verify=False
        )
        if r.status_code != 200:
            raise Exception(f"Rollback PUT failed HTTP {r.status_code}: {r.text[:200]}")
        logger.info(f"Rollback OK: {template_id[:8]}...")

    def get_feature_template(self, template_id):
        r = self.session.get(
            f"{self.host}/dataservice/template/feature/object/{template_id}",
            verify=False
        )
        if r.status_code != 200:
            raise Exception(f"GET feature template failed: {r.text}")
        return r.json()

    def get_inputs(self, template_id, device_uuid):
        r = self.session.post(
            f"{self.host}/dataservice/template/device/config/input",
            json={"templateId": template_id, "deviceIds": [device_uuid],
                  "isEdited": "false", "isMasterEdited": "false"},
            verify=False
        )
        if not r.text or not r.text.strip():
            return []
        try:
            return r.json().get("data", [])
        except Exception:
            return []

    def get_config_preview(self, template_id, device_row):
        r = self.session.post(
            f"{self.host}/dataservice/template/device/config/config/",
            json={"templateId": template_id, "device": device_row},
            verify=False
        )
        return r.text

    def attach_and_deploy(self, template_id, inputs, is_edited=False):
        payload = {
            "deviceTemplateList": [{
                "templateId":      template_id,
                "device":          inputs,
                "isEdited":        is_edited,
                "isMasterEdited":  False,
                "isDraftDisabled": False
            }]
        }
        r = self.session.post(
            f"{self.host}/dataservice/template/device/config/attachfeature",
            json=payload,
            verify=False
        )
        if r.status_code != 200:
            raise Exception(f"Attach failed HTTP {r.status_code}: {r.text[:200]}")
        action_id = r.json().get("id", "unknown")
        logger.info(f"Deploy triggered: {action_id}")
        return action_id

    def poll_task(self, action_id, timeout=180):
        for elapsed in range(5, timeout + 5, 5):
            time.sleep(5)
            r = self.session.get(
                f"{self.host}/dataservice/device/action/status/{action_id}",
                verify=False
            )
            if r.status_code != 200:
                continue
            data    = r.json()
            summary = data.get("summary", {})
            counts  = summary.get("count", {})
            status  = summary.get("status", "unknown")
            success = counts.get("Success", 0)
            failure = counts.get("Failure", 0)
            print(f"  [{elapsed:>3}s] {status:<12}  success={success}  failure={failure}")
            if status.lower() in ("done", "success"):
                return {"status": status, "success": success, "failure": failure, "data": data.get("data", [])}
        return {"status": "timeout", "success": 0, "failure": 0, "data": []}
