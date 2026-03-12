import logging
from src import state

logger = logging.getLogger("sdwan.uc2")

SIG_TYPE  = "cisco_secure_internet_gateway"
CRED_TYPE = "cisco_sig_credentials"
STATE_KEY = "uc2"


def run(client, cfg, force=False):
    uc2         = cfg["uc2"]
    template_id = uc2["device_template_id"]
    device_uuid = uc2["device_uuid"]
    sig_id      = uc2["sig_template_id"]
    cred_id     = uc2["sig_cred_id"]
    variables   = uc2["variables"]

    print("\nUSE CASE 2: Zscaler SIG Tunnel")
    print("-" * 50)
    logger.info("UC2 START")

    done, record = state.is_done(STATE_KEY)
    if done and not force:
        print("  ALREADY DEPLOYED - UC2 will not run again")
        print(f"  Deployed at : {record.get('deployed_at')}")
        print(f"  Template    : {record.get('template_id', '')[:16]}...")
        print("  Use --force to override and redeploy")
        logger.info("UC2 skipped - already deployed")
        return None, template_id, False

    import json
    template     = client.get_device_template(template_id)
    template_str = json.dumps(template)
    changed      = False

    sig_added = False
    for t in template.get("generalTemplates", []):
        if t.get("templateType") == "cisco_vpn":
            ft     = client.get_feature_template(t["templateId"])
            vpn_id = ft.get("templateDefinition", {}).get("vpn-id", {}).get("vipValue")
            if vpn_id == 0:
                if SIG_TYPE in template_str:
                    print("  SIG template already present under VPN0 - skipping")
                else:
                    t.setdefault("subTemplates", []).append(
                        {"templateId": sig_id, "templateType": SIG_TYPE}
                    )
                    print("  SIG template attached under VPN0")
                    logger.info(f"SIG attached: {sig_id[:8]}...")
                    changed   = True
                    sig_added = True
                break

    if not sig_added and SIG_TYPE not in template_str:
        print("  WARNING: VPN0 block not found - SIG not attached")
        logger.warning("VPN0 not found in device template")

    if CRED_TYPE in template_str:
        print("  SIG credentials already present - skipping")
    else:
        template["generalTemplates"].append({"templateId": cred_id, "templateType": CRED_TYPE})
        print("  SIG credentials attached")
        logger.info(f"SIG credentials attached: {cred_id[:8]}...")
        changed = True

    if changed:
        client.update_device_template(template_id, template)
        print("  Device template updated in vManage")
    else:
        print("  No template changes required")

    inputs = client.get_inputs(template_id, device_uuid)
    if not inputs:
        inputs = [{"csv-status": "completed", "csv-deviceId": device_uuid}]

    row = inputs[0]
    _apply_variables(row, variables)
    row["csv-status"] = "completed"
    logger.info("UC2 inputs ready")
    return inputs, template_id, changed


def _apply_variables(row, variables):
    from jinja2 import Environment, FileSystemLoader
    env      = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("variables.j2")
    rendered = template.render(variables=variables)
    logger.info(f"Rendered variables.j2:\n{rendered}")
    for key, value in variables.items():
        if value:
            row[key] = str(value)
            print(f"  Set: {key} = {value}")
            logger.info(f"  variable: {key}={value}")
