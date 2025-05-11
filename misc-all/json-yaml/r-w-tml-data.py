import yaml

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

yaml_file = open("test2.yaml", "w")

yaml_data = yaml.dump(intf_conf_data, yaml_file, indent=4) # Indent=4 says 4 spaces of indentation
yaml_file.close()

###### Reading from file #######################


yaml_file = open("test2.yaml", "r")

yaml_data = yaml.load(yaml_file)
print(yaml_data)

