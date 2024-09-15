
def sw_config(vlans, devices):
    for dev in devices:
        print("connecting to " + dev)
        print("conf t")
        for vlan in vlans:
            # print(vlan)
            # for k,v in vlan.items()
            vlan_id = vlan.get("id")
            name = vlan.get("name")
            print("vlan " + vlan_id)   
            #print(f"vlan {vlan_id}")
            print("name " + name)
            #print(f"name {name}")
        print("exit")
        print("\n")    
    


vlans = [{"id": "10", "name": "USERS"},
         {"id": "20", "name": "VOICE"},
         {"id": "30", "name": "WLAN"}
         
         ]

devices = ["switch1", "switch2", "switch3"]


sw_config(vlans, devices)


""" 
vlans = [{"id": "10", "name": "USERS"},
         {"id": "20", "name": "VOICE"},
         {"id": "30", "name": "WLAN"}
         
         ]

devices = ["switch1", "switch2", "switch3"]


for dev in devices:
    print("connecting to " + dev)
    print("conf t")
    for vlan in vlans:
        # print(vlan)
        # for k,v in vlan.items()
        vlan_id = vlan.get("id")
        name = vlan.get("name")
        print("vlan " + vlan_id)
        print("name " + name)
    print("exit")
    print("\n")

"""

