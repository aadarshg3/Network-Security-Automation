from func1 import config_gen

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