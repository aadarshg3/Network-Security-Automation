import yaml
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler




# sw_list = ["sw1", "sw2", "sw3"]
# sites_list = ["site-A", "site-B", "site-C"]
# intf_conf_data = [{
#     "intf_name": "gig0/1",
#     "desc": "Connected to server1",
#     "speed": 1000,
#     "duplex": "full"
# },
# {
#     "intf_name": "gig0/2",
#     "desc": "Connected to server2",
#     "speed": 1000,
#     "duplex": "full"
# },
# {
#     "intf_name": "gig0/3",
#     "desc": "Connected to server3",
#     "speed": 1000,
#     "duplex": "full"
# }                  
# ]

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
    'ip': '192.168.1.31',            # Replace with your switch's IP address
    'username': 'netg',            # Replace with your username
    'password': 'netg',         # Replace with your password
    'secret': 'enable_password',    # Replace with your enable/secret password
}




with open("conf-data.yaml", "r") as yaml_file:
    intf_conf_data = yaml.safe_load(yaml_file)
# print(intf_conf_data)  

  

env = Environment(loader=FileSystemLoader('.'))
template = env.get_template("intf-syntax.j2")

# python code to render config data into jinja2
rendered_output  = template.render(intf_conf_data)
# print(rendered_output)

conf_data = rendered_output.splitlines()
print(conf_data)

net_connect = ConnectHandler(**cisco_switch)
output = net_connect.send_config_set(conf_data)
print(output)


#########################################################################

with open("intf-conf-data.txt", "w") as ouptut_file:
    ouptut_file.write(rendered_output)

#==========Can used to get data in list form =============
    
# with open("intf-conf-data.txt", "r") as read_file:
#     config_data_list = read_file.readlines()  
# print(config_data_list)  
    
#==========above of end code=============
    



# intf_syntax = {
#     "intf_name": "interface {}",
#     "desc": "description {}",
#     "speed": "speed {}",
#     "duplex": "duplex {}"
# }

# for site in sites_list:
#     print("\n")
#     print("Configuring Site", site)
#     for sw in sw_list:
#         print("\n")
#         print("configuring", sw)
#         for item in intf_conf_data:
#             print(intf_syntax["intf_name"].format(item["intf_name"]))
#             print(intf_syntax["desc"].format(item["desc"]))
#             print(intf_syntax["speed"].format(item["speed"]))
#             print(intf_syntax["duplex"].format(item["duplex"]))
        

