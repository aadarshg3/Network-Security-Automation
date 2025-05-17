# Import required libraries
import yaml  # For reading YAML files
from getpass import getpass  # To securely prompt for password input
from jinja2 import Environment, FileSystemLoader  # For templating
from netmiko import ConnectHandler  # For SSH connections to network devices

# Prompt the user to enter their username
username = input("Username: ")

# Prompt for the password without echoing it to the screen
password = getpass("Password: ")

# -------- Load the device inventory --------
# Open the YAML inventory file named 'inv.yaml' in read mode
with open("inv.yaml") as f:
    inventory = yaml.safe_load(f)  # Load and parse the YAML content into a Python dictionary

# Extract the list of devices from the dictionary using the 'devices' key
devices = inventory["devices"]

# -------- Load VLAN data --------
# Open the VLAN data YAML file
with open("vlan.yaml") as yaml_file:
    vlan_data = yaml.safe_load(yaml_file)  # Load and parse VLAN configuration data

# -------- Prepare Jinja2 templating environment --------
# Create a FileSystemLoader to tell Jinja2 to look in the current directory (".") for templates
template_loader = FileSystemLoader(searchpath=".")

# Create a Jinja2 Environment using the loader
env = Environment(loader=template_loader)

# Load the Jinja2 template file named 'vlan.j2'
template = env.get_template("vlan.j2")

# -------- Render the VLAN configuration using the template --------
# Render the template using the VLAN data from 'vlan.yaml'
# 'device_data' is the variable name that will be used inside the template
rendered_config = template.render(device_data=vlan_data)

# -------- Prepare the config to send to devices --------
# Remove any leading/trailing whitespace and split the output into a list of lines
config_lines = rendered_config.strip().splitlines()

# -------- Send config to each device --------
# Loop through all devices in the inventory
for device in devices:
    # Print which device we're connecting to
    print(f"\nConnecting to {device['hostname']} ({device['host']})...")

    # Create an SSH connection to the device using Netmiko
    conn = ConnectHandler(
        device_type=device["device_type"],  # e.g., 'cisco_ios'
        host=device["host"],                # IP or hostname of the device
        username=username,                  # Username entered earlier
        password=password                   # Password entered earlier
    )

    # Print a message that we're sending the config
    print(f"Sending VLAN config to {device['hostname']}...")

    # Send the rendered VLAN configuration to the device
    print(conn.send_config_set(config_lines))

    # Close the SSH connection
    conn.disconnect()












############Sir-Code================

'''
import yaml
from netmiko import ConnectHandler
from jinja2 import FileSystemLoader, Environment

# Loading inventory information
inv = open("inv_multi.yaml", "r")
devices = yaml.safe_load(inv)

# Loading YAML data
sw_config_data = open("vlan.yaml", "r")
vlan_data = yaml.safe_load(sw_config_data)

# Load the Jinja2 template from file
template_loader = FileSystemLoader(searchpath=".")
env = Environment(loader=template_loader)
template = env.get_template("vlan.j2")

# Render the template with the data
rendered_output = template.render(device_data=vlan_data)
print(type(rendered_output))
config_list = rendered_output.splitlines()
print(config_list)

for device in devices:
    print("Connected to the device.", device["hostname"])

    net_connect = ConnectHandler(device_type=device['device_type'],host=device['host'],username=device['username'],password=device['password'])

    output = net_connect.send_config_set(config_list)
    # # output = net_connect.send_config_from_file('config_gen_data.conf')
    # print("configuration PUSH:")
    print(output)

    # # Disconnect from the device
    net_connect.disconnect()
    print("Disconnected from the device.")





'''























'''

import yaml
from getpass import getpass
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler

# Prompt user for credentials
username = input("Username: ")
password = getpass("Password: ")

# Load device inventory from YAML
with open("inv.yaml") as f:
    inventory = yaml.safe_load(f)

devices = inventory["devices"]

# Load VLAN configuration data from YAML
with open("vlan.yaml") as yaml_file:
    vlan_data = yaml.safe_load(yaml_file)  

# Set up Jinja2 template environment
template_loader = FileSystemLoader(searchpath=".")
env = Environment(loader=template_loader)
template = env.get_template("vlan.j2")  


# Render the VLAN config from template using correct key
rendered_config = template.render(device_data=vlan_data)

# Convert rendered configuration into list of lines
config_lines = rendered_config.strip().splitlines()
# print(config_lines)

# Deploy config to each device in inventory
for device in devices:
    print(f"\nConnecting to {device['hostname']} ({device['host']})...")
    conn = ConnectHandler(
        device_type=device["device_type"],
        host=device["host"],
        username=username,
        password=password
    )
    print(f"Sending VLAN config to {device['hostname']}...")
    print(conn.send_config_set(config_lines))
    conn.disconnect()


'''



























# import yaml
# from jinja2 import FileSystemLoader, Environment
# # from netmiko import ConnectHandler, Environment 

# # Load YAML data using 'with open' for safe file handling
# with open("vlan.yaml") as yaml_file:
#     sw_config_data = yaml.safe_load(yaml_file)

# # Set up the Jinja2 environment and load template
# template_loader = FileSystemLoader(searchpath=".")
# env = Environment(loader=template_loader)
# template = env.get_template("vlan.j2")

# # Render the template with the loaded YAML data
# rendered_output = template.render(device_data=sw_config_data)

# # Output the rendered configuration
# # print(rendered_output)

# # Optional: Break output into lines if needed
# config_list = rendered_output.splitlines()
# print(config_list)







'''

import yaml
from jinja2 import FileSystemLoader, Environment

# Read the YAML file
with open("vlan.yaml", "r") as intef_data_yaml_file:
    sw_config_data = yaml.safe_load(intef_data_yaml_file)  # Read YAML and
      convert into a Python list of dicts

# print("Loaded YAML Data:")
# print(sw_config_data)

# Set up the Jinja2 environment
template_loader = FileSystemLoader(searchpath=".")
env = Environment(loader=template_loader)
template = env.get_template("vlan.j2")

# Render the template with the data
rendered_output = template.render(data_list=sw_config_data)  # Correct: use data_list to match Jinja2 template
config_list = rendered_output.splitlines()

# Print the rendered configuration
print("\nRendered Configuration:")
for line in config_list:
    print(line)

'''