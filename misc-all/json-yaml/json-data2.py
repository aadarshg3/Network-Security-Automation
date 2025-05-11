import json

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

json_file = open("test2.json", "w")

json_data = json.dump(intf_conf_data, json_file, indent=4) # Indent=4 says 4 spaces of indentation
json_file.close()

###### Reading from file #######################


json_file = open("test2.json", "r")

json_data = json.load(json_file)
print(json_data)
