intf_config_data = {
    "intf": "Gigabit0/1", 
    "desc": "Connected to server-1",
    "speed": 1000,
    "duplex": "full"
}

intf_config_data_2 = {
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

intf_config_syntax_2 = {
    "intf": "interface {}", 
    "desc": "description {}",
    "speed": "speed {}",
    "duplex": "duplex {}"
}


def config_gen(intf_config_data, intf_config_syntax):
    temp = []
    for key in intf_config_data.keys():
        config = intf_config_syntax[key].format(intf_config_data[key])
        # print(config)
        temp.append(config)
    return temp  
def print_config(output):
    for item in output:
        print(item)  

output = config_gen(intf_config_data, intf_config_syntax)
print_config(output)


# /automation/Network-Security-Automation/python-auto-code/function














# for key, value in intf_config_data.items():
#     config = intf_config_syntax[key].format(intf_config_data[key])
#     print(config)

# for key, value in intf_config_data.items():
#     config = intf_config_syntax[key].format(value)
#     print(config)