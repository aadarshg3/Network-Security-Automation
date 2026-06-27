import yaml

device_info = {
    "vendor": "cisco",
    "model": "Catalyst-9300",
    "intf_info": {"intf_names": ["gig0/1", "gig0/2", "gig0/3"], "desc": "Connected to server-1", "speed": 1000}

}


yaml_file = open("test.yaml", "w")

yaml_data = yaml.dump(device_info, yaml_file, indent=4) # Indent=4 says 4 spaces of indentation
yaml_file.close()

########## Reading from yaml===================

yaml_file = open("test.yaml", "r")

my_data = yaml.load(yaml_file)
print(my_data)



# colon space (: )
# Hyphen space (- )