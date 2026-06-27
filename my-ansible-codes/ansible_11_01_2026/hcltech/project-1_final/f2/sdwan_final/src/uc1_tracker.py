import logging
from src import state

logger = logging.getLogger("sdwan.uc1")

TRACKER_TYPE = "cisco_tracker"
NAT_TYPE     = "cisco_nat"
STATE_KEY    = "uc1"


def run(client, cfg, force=False):
    uc1         = cfg["uc1"]
    template_id = uc1["device_template_id"]
    device_uuid = uc1["device_uuid"]
    tracker_id  = uc1["tracker_template_id"]
    nat_id      = uc1["nat_template_id"]
    variables   = uc1["variables"]

    print("\nUSE CASE 1: Tracker + NAT")
    print("-" * 50)
    logger.info("UC1 START")

    done, record = state.is_done(STATE_KEY)
    if done and not force:
        print("  ALREADY DEPLOYED - UC1 will not run again")
        print(f"  Deployed at : {record.get('deployed_at')}")
        print(f"  Template    : {record.get('template_id', '')[:16]}...")
        print("  Use --force to override and redeploy")
        logger.info("UC1 skipped - already deployed")
        return None, template_id, False

    template     = client.get_device_template(template_id)
    existing_ids = [t["templateId"] for t in template.get("generalTemplates", [])]
    changed      = False

    if tracker_id and tracker_id not in existing_ids:
        template["generalTemplates"].append({"templateId": tracker_id, "templateType": TRACKER_TYPE})
        print(f"  Tracker template attached")
        logger.info(f"Tracker attached: {tracker_id[:8]}...")
        changed = True
    else:
        print("  Tracker template already present - skipping")

    if nat_id and nat_id not in existing_ids:
        template["generalTemplates"].append({"templateId": nat_id, "templateType": NAT_TYPE})
        print(f"  NAT template attached")
        logger.info(f"NAT attached: {nat_id[:8]}...")
        changed = True
    else:
        print("  NAT template already present - skipping")

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
    logger.info("UC1 inputs ready")
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
