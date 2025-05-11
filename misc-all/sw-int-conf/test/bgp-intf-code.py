import yaml
from jinja2 import Environment, FileSystemLoader
import os
from netmiko import ConnectHandler


cisco_router = [{
    'device_type': 'cisco_ios',     # Device type for Cisco IOS devices
    'ip': '192.168.1.12',            # Replace with your switch's IP address
    'username': 'netg',            # Replace with your username
    'password': 'netg',         # Replace with your password
    'secret': 'enable_password',    # Replace with your enable/secret password
},
  {
    'device_type': 'cisco_ios',     # Device type for Cisco IOS devices
    'ip': '192.168.1.13',            # Replace with your switch's IP address
    'username': 'netg',            # Replace with your username
    'password': 'netg',         # Replace with your password
    'secret': 'enable_password',    # Replace with your enable/secret password
},
  {
    'device_type': 'cisco_ios',     # Device type for Cisco IOS devices
    'ip': '192.168.1.14',            # Replace with your switch's IP address
    'username': 'netg',            # Replace with your username
    'password': 'netg',         # Replace with your password
    'secret': 'enable_password',    # Replace with your enable/secret password
}              
                ]



with open("bgp_inv.yaml", "r") as yaml_file:
    bgp_intf_config = yaml.safe_load(yaml_file)
# print(bgp_intf_config)    


# with open("inven.yaml", "r") as yaml_file1:
#     cred = yaml.safe_load(yaml_file1)
    
    
template_loader = FileSystemLoader(searchpath=('.'))
env = Environment(loader=template_loader)
template = env.get_template("inf-syn2.j2")

# user = os.getenv("USERNAME")
# user_password = os.getenv("PASSWORD")



rendered_output = template.render(bgp=bgp_intf_config)
# print(rendered_output)
config_list = rendered_output.splitlines()
print(config_list)

# for router in cisco_router:
#     net_connect = ConnectHandler(**router)
#     net_connect.enable()
#     output = net_connect.send_config_set(config_list)
#     print(output)
#     net_connect.disconnect()
    