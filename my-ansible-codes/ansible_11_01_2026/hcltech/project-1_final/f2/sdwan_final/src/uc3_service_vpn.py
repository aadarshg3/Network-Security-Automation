import json
import logging
from src import state

logger = logging.getLogger("sdwan.uc3")

STATE_KEY = "uc3"


def run(client, cfg, force=False):
    uc3         = cfg["uc3"]
    template_id = uc3["device_template_id"]
    device_uuid = uc3["device_uuid"]
    variables   = uc3["variables"]

    print("\nUSE CASE 3: Service VPN Templates + BGP")
    print("-" * 50)
    logger.info("UC3 START")

    done, record = state.is_done(STATE_KEY)
    if done and not force:
        print("  ALREADY DEPLOYED - UC3 will not run again")
        print(f"  Deployed at : {record.get('deployed_at')}")
        print(f"  Template    : {record.get('template_id', '')[:16]}...")
        print("  Use --force to override and redeploy")
        logger.info("UC3 skipped - already deployed")
        return None, template_id, False

    template     = client.get_device_template(template_id)
    template_str = json.dumps(template)
    changed      = False

    blocks = [
        {
            "label":      "PEPguest VPN10",
            "templateId": uc3["pepguest_vpn_id"],
            "templateType": "cisco_vpn",
            "subTemplates": [
                {"templateId": uc3["pepguest_subif_id"], "templateType": "cisco_vpn_interface"}
            ],
        },
        {
            "label":      "PEPiNET VPN20",
            "templateId": uc3["pepinet_vpn_id"],
            "templateType": "cisco_vpn",
            "subTemplates": [
                {"templateId": uc3["pepinet_subif_id"], "templateType": "cisco_vpn_interface"}
            ],
        },
        {
            "label":      "Corporate VPN30 + BGP",
            "templateId": uc3["corporate_vpn_id"],
            "templateType": "cisco_vpn",
            "subTemplates": [
                {"templateId": uc3["corporate_subif_id"], "templateType": "cisco_vpn_interface"},
                {"templateId": uc3["corporate_bgp_id"],   "templateType": "cisco_bgp"},
            ],
        },
    ]

    for block in blocks:
        label = block.pop("label")
        if block["templateId"] and block["templateId"] in template_str:
            print(f"  {label}: already attached - skipping")
        elif block["templateId"]:
            template["generalTemplates"].append(block)
            template_str = json.dumps(template)
            print(f"  {label}: attached")
            logger.info(f"Attached {label}: {block['templateId'][:8]}...")
            changed = True
        else:
            print(f"  {label}: template ID not set - skipping")

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
    logger.info("UC3 inputs ready")
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
