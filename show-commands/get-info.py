import yaml
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler



# yaml_file = open("test.yaml", "w")
# yaml_data = yaml.dump(device_info, yaml_file, indent=4) # Indent=4 says 4 spaces of indentation
# yaml_file.close()
########## Reading from yaml===================

# yaml_file = open("conf_data.yaml", "r")
# intf_conf_data = yaml.load("yaml_file")
# yaml_file.close()

#########################################################################
cisco_switch = {
    'device_type': 'cisco_ios',     # Device type for Cisco IOS devices
    'ip': '192.168.1.211',            # Replace with your switch's IP address
    'username': 'netg',            # Replace with your username
    'password': 'netg',         # Replace with your password
    'secret': 'enable_password',    # Replace with your enable/secret password
}


temp = []

net_connect = ConnectHandler(**cisco_switch)
output1 = net_connect.send_command("show ip interface brief", use_textfsm=True)

# output = net_connect.send_command("show ip interface brief")
# output = net_connect.send_command("show vlan brief")


# print(output1)

temp.append(output1)
output2 = net_connect.send_command("show vlan brief", use_textfsm=True)
temp.append(output2)
print(output2)
# print(type(output))



