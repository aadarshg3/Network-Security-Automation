import yaml
from jinja2 import FileSystemLoader, Environment
from netmiko import ConnectHandler


cisco_router = {
    'device_type': 'cisco_ios',     # Device type for Cisco IOS devices
    'ip': '192.168.1.12',            # Replace with your switch's IP address
    'username': 'netg',            # Replace with your username
    'password': 'netg',         # Replace with your password
    'secret': 'enable_password',    # Replace with your enable/secret password
}



with open("bgpconfig-data.yaml", "r") as yaml_file:
    bgpconfig = yaml.safe_load(yaml_file)
# print(bgpconfig)
    
# env = Environment(FileSystemLoader(searchpath=(".")))
# =====>>>> line 9 & 10 are same as 12

template_loader = FileSystemLoader(searchpath=".")
env = Environment(loader=template_loader)

template = env.get_template("bgpjinja.j2") 
# print(template)

rendered_output = template.render(bgp=bgpconfig)
# print(rendered_output)
config_data = rendered_output.splitlines()
print(config_data)

net_connect = ConnectHandler(**cisco_router)   
output = net_connect.send_config_set(config_data)
print(output)