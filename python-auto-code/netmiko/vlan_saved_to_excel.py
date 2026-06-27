from netmiko import ConnectHandler
import pandas as pd
import yaml
from getpass import getpass

# Prompt for login credentials
username = input("Username: ")
password = getpass("Password: ")

# Load inventory from YAML file
with open("inv.yaml") as file:
    inventory = yaml.safe_load(file)

devices = inventory["devices"]

# Dictionary to store data
device_vlan_info = {}

# Loop through all devices
for device in devices:
    hostname = device.get("hostname", device.get("host"))
    print("Connecting to", hostname)

    conn = ConnectHandler(
        device_type=device["device_type"],
        host=device["host"],
        username=username,
        password=password
    )

    output = conn.send_command("show vlan brief", use_textfsm=True)
    device_vlan_info[hostname] = output

    conn.disconnect()
    print("Disconnected from", hostname)

# Save to Excel
with pd.ExcelWriter("vlan_report.xlsx", engine="openpyxl") as writer:
    for device, vlan_data in device_vlan_info.items():
        df = pd.DataFrame(vlan_data)
        df.to_excel(writer, sheet_name=device, index=False)

print("VLAN report saved to vlan_report.xlsx")

