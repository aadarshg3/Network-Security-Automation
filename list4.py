
config_list_access = ["switchport mode access", "switchport access vlan 10"]

config_list_trunk = ["switchport mode trunk", "switchport trunk allowed vlan add 10"]

intf_list = ["gi0/1", "gi0/2", "gi0/3", "gi0/4"]
device_list = ["switch1", "switch2", "switch3", "switch4"]

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

"""
############ Output ##############

root@Aadarshg3:~/devnet/autobundle-may# python3 list4.py 
logging to switch1
interface gi0/1
switchport mode trunk
switchport trunk allowed vlan add 10
interface gi0/2
switchport mode trunk
switchport trunk allowed vlan add 10
interface gi0/3
switchport mode access
switchport access vlan 10
interface gi0/4
switchport mode access
switchport access vlan 10
logging to switch2
interface gi0/1
switchport mode trunk
switchport trunk allowed vlan add 10
interface gi0/2
switchport mode trunk
switchport trunk allowed vlan add 10
interface gi0/3
switchport mode access
switchport access vlan 10
interface gi0/4
switchport mode access
switchport access vlan 10
logging to switch3
interface gi0/1
switchport mode trunk
switchport trunk allowed vlan add 10
interface gi0/2
switchport mode trunk
switchport trunk allowed vlan add 10
interface gi0/3
switchport mode access
switchport access vlan 10
interface gi0/4
switchport mode access
switchport access vlan 10
logging to switch4
interface gi0/1
switchport mode trunk
switchport trunk allowed vlan add 10
interface gi0/2
switchport mode trunk
switchport trunk allowed vlan add 10
interface gi0/3
switchport mode access
switchport access vlan 10
interface gi0/4
switchport mode access
switchport access vlan 10
root@Aadarshg3:~/devnet/autobundle-may# 


"""








"""

config_list_access = ["switchport mode access", "switchport access vlan 10"]

config_list_trunk = ["switchport mode trunk", "switchport trunk allowed vlan add 10"]

intf_list = ["gi0/1", "gi0/2", "gi0/3", "gi0/4"]


# print(config_list)

for intf in intf_list:
    print("interface", intf)
    if intf == "gi0/1" or intf == "gi0/2":
        for conf in config_list_trunk:
            print(conf)
    else:
        for conf in config_list_access:
            print(conf)        
            

"""







            
            
"""
#######
root@Aadarshg3:~/devnet/autobundle-may# 
root@Aadarshg3:~/devnet/autobundle-may# 
root@Aadarshg3:~/devnet/autobundle-may# 
root@Aadarshg3:~/devnet/autobundle-may# python3 list4.py 
interface gi0/1
switchport mode trunk
switchport trunk allowed vlan add 10
interface gi0/2
switchport mode trunk
switchport trunk allowed vlan add 10
interface gi0/3
switchport mode access
switchport access vlan 10
interface gi0/4
switchport mode access
switchport access vlan 10
root@Aadarshg3:~/devnet/autobundle-may# 

"""            