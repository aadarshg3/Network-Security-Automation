import yaml
from jinja2 import FileSystemLoader, Environment
import os
from netmiko import ConnectHandler


with open("bgp_data.yaml", "r") as yaml_file:
    intf_conf_data = yaml.safe_load(yaml_file)
# print(intf_conf_data)   

with open("bgp_inv.yaml", "r") as yaml_file:
    devices = yaml.safe_load(yaml_file)
# print(devices)   

template_loader = FileSystemLoader(searchpath=".")
env = Environment(loader=template_loader)
template = env.get_template("bgp_temp.j2")


user = os.getenv("USERNAME")    
user_password = os.getenv("PASSWORD")


for device in devices:
    rendered_output = template.render(conf_data=intf_conf_data["bgp_conf"][device["hostname"]])
    config_list = rendered_output.splitlines()
    print(config_list)


    net_connect = ConnectHandler(device_type=device["device_type"], host=device["host"],username=user,password=user_password)    
    output = net_connect.send_config_set(config_list)
    print(output)
