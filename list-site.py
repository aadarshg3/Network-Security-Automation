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


