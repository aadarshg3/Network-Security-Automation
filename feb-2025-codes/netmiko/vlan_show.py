from netmiko import ConnectHandler
import yaml
from getpass import getpass

# Prompt for credentials
username = input("Username: ")
password = getpass("Password: ")

# Load inventory from YAML file
with open("inv.yaml") as f:
    inventory = yaml.safe_load(f)

devices = inventory["devices"]
print(devices)

# Dictionary to store VLAN information
device_vlan_info = {}

# Loop through each device in the inventory
for device in devices:
    hostname = device.get("hostname", device.get("host"))
    print("Connecting to", hostname, "(", device["host"], ")")

    # Establish SSH connection
    conn = ConnectHandler(
        device_type=device["device_type"],
        host=device["host"],
        username=username,
        password=password
    )

    # Run 'show vlan brief' and parse output
    print("Running 'show vlan brief' on", hostname)
    output = conn.send_command("show vlan brief", use_textfsm=True)

    # Store output in dictionary
    device_vlan_info[hostname] = output

    # Print VLAN summary
    print("VLAN Summary for", hostname)
    if output:
        for vlan in output:
            vlan_id = vlan.get('vlan_id', 'N/A')
            name = vlan.get('name', 'N/A')
            status = vlan.get('status', 'N/A')
            print("  VLAN ID:", vlan_id, "Name:", name, "Status:", status)
    else:
        print("  No VLAN data returned.")

    # Disconnect SSH session
    conn.disconnect()
    print("Disconnected from", hostname)

# Print final summary
print("Final VLAN Info Summary:")
for device_name, vlans in device_vlan_info.items():
    print("Device:", device_name)
    for vlan in vlans:
        print("  VLAN ID:", vlan.get('vlan_id'), "| Name:", vlan.get('name'), "| Status:", vlan.get('status'))
