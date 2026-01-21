import json
import openpyxl

# Load the parsed interfaces data from the JSON file
with open("/mnt/d/networking/network-automation/boot-camp/ansible-may-24/Ansible/Playbooks/parsed_interfaces.json", "r") as f:
    data = json.load(f)

# Create a new workbook and sheet
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Interface Status"

# Define column headers
headers = ['Switch Name', 'Interface', 'Status', 'Protocol', 'IP Address']
ws.append(headers)

# Populate the rows with the parsed interface data
for interface, details in data['interface'].items():
    switch_name = "switch1"  # You can adjust this if needed or dynamically fetch it from the Ansible inventory
    status = details.get('status', 'N/A')
    protocol = details.get('protocol', 'N/A')
    ip_address = details.get('ip_address', 'N/A')

    # Append each row of data to the worksheet
    ws.append([switch_name, interface, status, protocol, ip_address])

# Save the Excel file to a specific path
output_file = "/mnt/d/networking/network-automation/boot-camp/ansible-may-24/Ansible/Playbooks/switch_interfaces_report.xlsx"
wb.save(output_file)

# Print confirmation message
print(f"Report saved as {output_file}")
