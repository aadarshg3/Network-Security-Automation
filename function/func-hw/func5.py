def switch_configuration(config_list_access, config_list_trunk,intf_list, device_list):
    for dev in device_list:
        print("logging to" , dev)

        for intf in intf_list:
            print("interface", intf)
            if intf == "gi0/1" or intf == "gi0/2":
                for conf in config_list_trunk:
                    print(conf)
            else:
                for conf in config_list_access:
                    print(conf)   
    

device_list = ["switch1", "switch2", "switch3", "switch4"]    
config_list_access = ["switchport mode access", "switchport access vlan 10"]

config_list_trunk = ["switchport mode trunk", "switchport trunk allowed vlan add 10"]

intf_list = ["gi0/1", "gi0/2", "gi0/3", "gi0/4"]


output = switch_configuration(config_list_access, config_list_trunk,intf_list, device_list)
print(output)

# testtdasf
