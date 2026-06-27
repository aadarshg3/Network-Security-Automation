def configure_sites(sites, switches, intf_conf, syntax):
    config_output = []
    
    for site in sites:
        config_output.append(f"\nConfiguring Site {site}")
        for switch in switches:
            config_output.append(f"\nConfiguring {switch}")
            for item in intf_conf:
                config_output.append(syntax["intf_name"].format(item["intf_name"]))
                config_output.append(syntax["desc"].format(item["desc"]))
                config_output.append(syntax["speed"].format(item["speed"]))
                config_output.append(syntax["duplex"].format(item["duplex"]))
            config_output.append("")
    
    return config_output

# Example usage:
sw_list = ["sw1", "sw2", "sw3"]
sites_list = ["site-A", "site-B", "site-C"]
intf_conf_data = [
    {
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

intf_syntax = {
    "intf_name": "interface {}",
    "desc": "description {}",
    "speed": "speed {}",
    "duplex": "duplex {}"
}

# Call the function and store the returned configuration
config = configure_sites(sites_list, sw_list, intf_conf_data, intf_syntax)

# Print the configuration
for line in config:
    print(line)