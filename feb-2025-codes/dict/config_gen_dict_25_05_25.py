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



# intf_data = "gig0/10"
intf_config_data["intf"]

# intf_syntax = "interface {}"
intf_config_syntax["intf"]

# config = intf_syntax.format(intf_data)

config = intf_config_syntax["intf"].format(intf_config_data["intf"])
print(config)
config = intf_config_syntax["desc"].format(intf_config_data["desc"])
print(config)
config = intf_config_syntax["speed"].format(intf_config_data["speed"])
print(config)
config = intf_config_syntax["duplex"].format(intf_config_data["duplex"])
print(config)