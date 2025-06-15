

intf_list = ["gig0/1", "gig0/2", "gig0/3"]

access_intf_config = ["description user port",
               "switchport mode access", 
               "switchport access vlan 10", 
               "speed 1000", "duplex full"
               ]

trunk_intf_config = ["description user port",
               "switchport mode trunk", 
               "switchport allowed vlan add 10", 
               "speed 1000", "duplex full"
               ]

for intf in intf_list:
    print("!")
    print("interface", intf)
    if intf == "gig0/2":
        # print("interface", intf)
        for config in trunk_intf_config:
            print(" ", config)
    else:        
        # print("interface", intf)
        for config in access_intf_config:
            print(" ", config)
    