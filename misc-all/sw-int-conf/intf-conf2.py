import yaml
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler



#########################################################################
cisco_switch = {
    'device_type': 'cisco_ios',     # Device type for Cisco IOS devices
    'ip': '192.168.1.9',            # Replace with your switch's IP address
    'username': 'netg',            # Replace with your username
    'password': 'netg',         # Replace with your password
    'secret': 'enable_password',    # Replace with your enable/secret password
}




with open("conf-data2.yaml", "r") as yaml_file:
    intf_conf_data = yaml.safe_load(yaml_file)
# print(intf_conf_data)  

  

env = Environment(loader=FileSystemLoader('.'))
template = env.get_template("inf-syn2.j2")

# python code to render config data into jinja2
rendered_output  = template.render(intf_conf_data=intf_conf_data) # intf_conf_data --> ye list of dict hai isiliye equals to hua
# print(rendered_output)

conf_data = rendered_output.splitlines()
print(conf_data)

net_connect = ConnectHandler(**cisco_switch)
output = net_connect.send_config_set(conf_data)
print(output)


#########################################################################

# with open("intf-conf-data.txt", "w") as ouptut_file:
#     ouptut_file.write(rendered_output)

