import yaml
from pprint import pprint

yaml_data = open("intf_config-data.yaml", "r")

config_info = yaml.safe_load(yaml_data)

# pprint(config_info)
yaml_data.close()

added_item = {
    'desc': 'Connected to server 10',
    'duplex': 'full',
    'intf_name': 'fa0/10',
    'speed': 1000
}

config_info.append(added_item)

# pprint(config_info)

f2 = open("data/config-data.yaml", "w")
yaml.dump(config_info, f2)
