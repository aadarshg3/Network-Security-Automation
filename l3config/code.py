import os
import yaml
from netmiko import ConnectHandler
from jinja2 import FileSystemLoader, Environment

file = open("data.yml", 'r')
data = yaml.safe_load(file)

file = open("inv.yml", 'r')
devices = yaml.safe_load(file)

# Load the Jinja2 template from file
template_loader = FileSystemLoader(searchpath=".")
env = Environment(loader=template_loader)
template = env.get_template("template.j2")

# Get the value of the environment variable 'MY_VARIABLE'
user = os.getenv('USERNAME')
user_password = os.getenv('PASSWORD')

for device in devices:
    # Render the template with the data
    rendered_output = template.render(conf_data=data["bgp_conf"][device["hostname"]])
    config_list = rendered_output.splitlines()
    print(config_list)
    
    print("Connected to the device.", device["hostname"])
    print(device["hostname"])
    net_connect = ConnectHandler(device_type=device['device_type'],host=device['host'],username=user,password=user_password)

    output = net_connect.send_config_set(config_list)
    # output = net_connect.send_config_from_file('config_gen_data.conf')
    print("configuration PUSH:")
    print(output)

    # Disconnect from the device
    net_connect.disconnect()
    print("Disconnected from the device.")
