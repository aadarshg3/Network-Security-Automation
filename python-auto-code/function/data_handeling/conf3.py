


import yaml

# Convert Python dictionary to YAML
devices = [
    {"name": "fw01", "ip": "192.168.1.1"},
    {"name": "fw02", "ip": "192.168.1.2"}
]

yaml_data = yaml.dump(devices)
print(yaml_data)
print(type(yaml_data))
# print(yaml_data)













# import json

# json_data = '''
# {
#   "devices": [
#     {"name": "fw01", "ip": "192.168.1.1"},
#     {"name": "fw02", "ip": "192.168.1.2"}
#   ]
# }
# '''

# data = json.loads(json_data)  # Convert JSON string to Python dict
# # print(type(data))
# for device in data["devices"]:
#     print(device["name"], device["ip"])




