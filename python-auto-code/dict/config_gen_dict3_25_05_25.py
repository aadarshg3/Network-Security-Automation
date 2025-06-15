intf_config_data_list = [{
    "intf": "Gigabit0/1", 
    "desc": "Connected to server-1",
    "speed": 1000,
    "duplex": "full"
},
{
    "intf": "Gigabit0/2", 
    "desc": "Connected to server-2",
    "speed": 1000,
    "duplex": "full"
},
{
    "intf": "Gigabit0/3", 
    "desc": "Connected to server-3",
    "speed": 1000,
    "duplex": "full"
},
{
    "intf": "Gigabit0/4", 
    "desc": "Connected to server-4",
    "speed": 1000,
    "duplex": "full"
}


]

intf_config_syntax = {
    "intf": "interface {}", 
    "desc": "description {}",
    "speed": "speed {}",
    "duplex": "duplex {}"
}


# for key, value in intf_config_data.items():
#     config = intf_config_syntax[key].format(intf_config_data[key])
#     print(config)


for intf_config_data in intf_config_data_list:
    for key in intf_config_data.keys():
        config = intf_config_syntax[key].format(intf_config_data[key])
        print(config)


