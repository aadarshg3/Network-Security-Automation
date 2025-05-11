import yaml
import json
from jinja2 import FileSystemLoader, Environment
from netmiko import ConnectHandler
import os

# =============================================
# cisco_switch = {
#     'device_type': 'cisco_ios',     # Device type for Cisco IOS devices
#     'ip': '192.168.1.211',            # Replace with your switch's IP address
#     'username': 'netg',            # Replace with your username
#     'password': 'netg',         # Replace with your password
#     'secret': 'enable_password',    # Replace with your enable/secret password
# }


# yaml_file = open("hw1.yaml", "w")
# yaml_data = yaml.dump(intf_conf_data, yaml_file, indent=4)
# yaml_file.close()


# yaml_file = open("test.json", "r")

# yaml_read_file = json.load(yaml_file)
# print(yaml_read_file)


# =====================================================
# open yaml file in python code

with open("hw1.yaml", "r") as yaml_file:
    intf_conf_data = yaml.safe_load(yaml_file)
# print(intf_conf_data)   

with open("inven.yaml", "r") as yaml2_file:
    devices = yaml.safe_load(yaml2_file)
# print(devices)    
    
# =====================================================
# Load the Jinja2 template from file
    
template_loader = FileSystemLoader(searchpath=("."))
env = Environment(loader=template_loader)
template = env.get_template("syn.j2")

# =====================================================
# Get the value of the environment variable 'MY_VARIABLE'

user = os.getenv("USERNAME")
user_password = os.getenv("PASSWORD")

# export USERNAME='your_username'  ===> run this on linux
# export PASSWORD='your_password'  ===> run this on linux

rendered_output = template.render(intf_conf_data=intf_conf_data)
# print(type(rendered_output))

conf_data = rendered_output.splitlines()
# print(conf_data)

net_connect = ConnectHandler(device_type=devices["device_type"], host = devices["host"], username=user, password=user_password )


output = net_connect.send_config_set(conf_data)
print(output)

# Disconnect from the device
net_connect.disconnect()
print("Disconnected from the device.")



# net_connect = ConnectHandler(**cisco_switch)
# output = net_connect.send_config_set(conf_data)
# print(output)


# net_connect = ConnectHandler(device_type=device['device_type'],host=device['host'],username=user,password=user_password)

#     output = net_connect.send_config_set(config_list)
#     # output = net_connect.send_config_from_file('config_gen_data.conf')
#     print("configuration PUSH:")
#     print(output)

#     # Disconnect from the device
#     net_connect.disconnect()
#     print("Disconnected from the device.")









