import re
import openpyxl
import yaml
from netmiko import ConnectHandler

# Load device details from YAML file
with open('device-detail.yaml', 'r') as yaml_file:
    device_data = yaml.safe_load(yaml_file)

routers = device_data['routers']

# Create an Excel workbook
wb = openpyxl.Workbook()

# Regular expression to match the output format of 'show ip interface brief'
pattern = re.compile(r"(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(administratively\sdown|up|down)\s+(\S+)")

# Iterate over the routers and create one sheet per router
for idx, router in enumerate(routers):
    # Create a new sheet for each router
    sheet_name = router['sheet_name']
    
    if idx == 0:
        ws = wb.active
        ws.title = sheet_name
    else:
        ws = wb.create_sheet(title=sheet_name)

    # Write the header row in the Excel sheet
    header = ["Interface", "IP-Address", "OK?", "Method", "Status", "Protocol"]
    ws.append(header)

    # Create a new dictionary excluding the sheet_name for connection
    connection_params = {key: router[key] for key in router if key != 'sheet_name'}

    # Connect to the router
    net_connect = ConnectHandler(**connection_params)
    net_connect.enable()  # Enter enable mode

    # Execute the command 'show ip interface brief'
    output = net_connect.send_command('show ip interface brief')
    print(f"Interface Status for {sheet_name} ({router['host']}):\n", output)

    # Parse the output using regex and write to the respective sheet
    for line in output.splitlines()[1:]:  # Skip the header line
        match = pattern.match(line)
        if match:
            interface_data = list(match.groups())  # Extract the parsed data
            ws.append(interface_data)  # Append the row to the sheet

    net_connect.disconnect()

# Save the Excel file with 3 different sheets
wb.save("interface_status_multiple_sheets.xlsx")
print("Interface status has been saved to 'interface_status_multiple_sheets.xlsx' with 3 different sheets.")
