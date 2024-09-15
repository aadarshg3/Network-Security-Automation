import json
import yaml

# sw_list = ["sw1", "sw2", "sw3"]

# sites_list = ["site-A", "site-B", "site-C"]

intf_conf_data = [{
    "intf_name": "gig0/1",
    "desc": "Connected to server1",
    "speed": 1000,
    "duplex": "full"
},
{
    "intf_name": "gig0/2",
    "desc": "Connected to server2",
    "speed": 1000,
    "duplex": "full"
},
{
    "intf_name": "gig0/3",
    "desc": "Connected to server3",
    "speed": 1000,
    "duplex": "full"
}                  
]

# json_file = open("file1.json", "w")
# json_data = json.dump(intf_conf_data, json_file, indent=4)
# json_file.close()

# #=========Read from Json File=============

# json_read_file = open("file1.json", "r")
# json_read_data = json.load(json_read_file)
# print(json_read_data)



#=====================YAML COnfiguration=======================

yaml_file = open("test1.yaml", "w")
yaml_data = yaml.dump(intf_conf_data, yaml_file, indent=4)
yaml_file.close()

# ============read from YAML============

yaml_read_file = open("test1.yaml", "r")
yaml_read_data = yaml.load(yaml_read_file)
print(yaml_read_data)