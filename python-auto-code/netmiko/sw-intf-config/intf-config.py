import yaml
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler 

cisco_switch = {
    "device_type": "cisco_ios",
    "host": "192.168.200.151",  # Replace with your switch's IP address
    "username": "netg",    # Replace with your username
    "password": "netg",  # Replace with your password
}

with open("conf-data.yaml", 'r') as yaml_file:
    intf_conf_data_new = yaml.safe_load(yaml_file)

# print(intf_conf_data)

env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('intf-syntax.j2')

# Python code to render config data into jinja2 template to 
rendered_output = template.render(intf_conf_data=intf_conf_data_new) # passing keyword variable arguments
# print(rendered_output)
conf_data = rendered_output.splitlines()
print(conf_data)

net_connect = ConnectHandler(**cisco_switch)
output = net_connect.send_config_set(conf_data)
print(output)

