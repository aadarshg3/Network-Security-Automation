
def config_gen(sw_config_data, sw_config_syntax):  # ===========> take inputs
    conf_list = []     
    for conf in sw_config_data:
        # print("!")
        # print(conf)
        for k, v in conf.items():
            rendered_config = sw_config_syntax[k].format(v)
            # print(rendered_config)
            # print("!!!!!!!!!!!!")
            conf_list.append(rendered_config)
    return conf_list        # ================================> Return Values

# print(conf_list) ====> scope is only function level XXXXXXXXX
# print(config_gen) XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX


sw_config_data_1 = [
    {
    "intf": "ge0/10",
    "desc": "connected to user port",
    "speed": 1000,
    "duplex": "full"
    },
    {
    "intf": "ge0/20",
    "desc": "connected to server",
    "speed": "auto",
    "duplex": "half"
    },
    {
    "intf": "ge0/30",
    "desc": "connected to user port",
    "speed": 1000,
    "duplex": "full"
    }   
]
sw_config_syntax_1 = {
    "intf": "interface {}",
    "desc": "description {}",
    "speed": "speed {}",
    "duplex": "duplex {}"
}


output = (config_gen(sw_config_data_1, sw_config_syntax_1))  # Positional Arguments
print(output)
print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

# for item in output:
#     print(item)














"""

sw_config_data = [
    {
    "intf": "ge0/1",
    "desc": "connected to user port",
    "speed": 1000,
    "duplex": "full"
    },
    {
    "intf": "ge0/2",
    "desc": "connected to server",
    "speed": "auto",
    "duplex": "half"
    },
    {
    "intf": "ge0/3",
    "desc": "connected to user port",
    "speed": 1000,
    "duplex": "full"
    }   
]

sw_config_syntax = {
    "intf": "interface {}",
    "desc": "description {}",
    "speed": "speed {}",
    "duplex": "duplex {}"
}

for conf in sw_config_data:
    print("!")
    # print(conf)
    for k, v in conf.items():
        print(sw_config_syntax[k])

def config_gen(sw_config_data, sw_config_syntax):
    conf_list = []
    for conf in sw_config_data:
        # print("!")
        # print(conf)
        for k, v in conf.items():
            rendered_config = sw_config_syntax[k].format(v)
            # print(rendered_config)
            # print("!!!!!!!!!!!!")
            conf_list.append(rendered_config)
    return conf_list 

# print(conf_list) ====> scope is only function level XXXXXXXXX
# print(config_gen) XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

output = (config_gen(sw_config_data, sw_config_syntax))
print(output)
print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
output = (config_gen(sw_config_data, sw_config_syntax))
print(output)
print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
output = (config_gen(sw_config_data, sw_config_syntax))
print(output)
print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")



# for item in output:
#     print(item)



"""