#!/usr/bin/env python3

# def get_commands(vlan_id, vlan_name):


vlans = [{"id": "10", "name": "USERS"},
         {"id": "20", "name": "VOICE"},
         {"id": 30, "name": "WLAN"}
         
         ]

devices = ["switch1", "switch2", "switch3"]

# commands = []

# commands = commands.append("vlan" +  )

# vlan 10
# name users
# vlan 20
# name voice
# vlan 30
# name wlan


""" 
for sw in devices:
    print("++","configuring ", sw, "++", "\n")
    print("conf t")
    for vlan in vlans:
        vlan_id = vlan["id"]
        vlan_name = vlan["name"]
        print(f"vlan {vlan_id}")
        print(f"name {vlan_name}")
    print("exit", "\n")

  """       







""" def print_vendor(net_vendor):  # ======> function
    print(net_vendor)  # ====> Operation

vendors = ["arista", "juniper", "big_switch", "cisco"]

for vendor in vendors:
    print_vendor(vendor)
     """