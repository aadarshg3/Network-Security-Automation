intf_config_data = {
    "intf": "Gigabit0/1", 
    "desc": "Connected to server-1",
    "speed": 1000,
    "duplex": "full"
}

intf_config_syntax = {
    "intf": "interface {}", 
    "desc": "description {}",
    "speed": "speed {}",
    "duplex": "duplex {}"
}


# for key, value in intf_config_data.items():
#     config = intf_config_syntax[key].format(intf_config_data[key])
#     print(config)

# for key, value in intf_config_data.items():
#     config = intf_config_syntax[key].format(value)
#     print(config)

for key in intf_config_data.keys():
    config = intf_config_syntax[key].format(intf_config_data[key])
    print(config)


