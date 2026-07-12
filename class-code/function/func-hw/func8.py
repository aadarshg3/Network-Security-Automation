""" def switch_config(inventory,vlan1,vlan2):
    inventory.append("")
    # print(inventory)
    for device in inventory:
        print("Connecting to", device)
        print("config t")
        if device == "Sw1" or device == "Sw2":
            for vlan in vlan1:
                print("vlan", vlan)
        else:
            for vlan in vlan2:
                print("vlan", vlan)
        print("Configuration complete for", device)
        
        
inventory1 = ["Sw1", "Sw2", "Sw3", "Sw4"]
vlan1 = ["10", "20", "30"]
vlan2 = ["100", "200", "300"] 
print(inventory1)
switch_config(inventory1,vlan1,vlan2)
print(inventory1)

 """
 
"""  
def add(a):
    a = a + 10
    print(a)
    
a = 10

print(a)     
add(a)
print(a)
 """





    
    
    
    