vlans = [10, 20, 30, 40]
switches = ["sw1", "sw2", "sw3"] 
# generate config for all switches
sites = ["site-1", "site-2", "site-3"]
# generate config for sites

for site in sites:
    print(f"#############configuring {site}############")
    for switch in switches:
        print(f"========config on switch:{switch}======")
        for vlan in vlans:
            print(f"vlan {vlan}")
            print(f"  name vlan_{vlan}")


