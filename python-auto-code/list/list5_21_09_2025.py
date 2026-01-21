# trunk and access port configuration:

trunk_port_config = ["switchport", "switchport mode trunk", "switchport trunk allowed vlan add 10"]
access_port_config = ["switchport", "switchport mode access", "switchport access vlan 10"]

interfaces = ["Ethernet0/1", "Ethernet0/2", "Ethernet0/3", "Ethernet0/4"]

for interface in interfaces:
    if interface == "Ethernet0/1" or interface == "Ethernet0/2":
        print(f"interface { interface }")
        for config in trunk_port_config:
            print(config)
else:
    print(f"interface {interface}")
    for config in access_port_config:
        print(config)
        