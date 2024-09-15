# generate vlan config and write to txt file

vlan_file = open("vlan_config_data.conf", "w")

for vlan_id in range(2, 11):
    # print(f"vlan {vlan_id}")
    # print(f"name vlan_{vlan_id}")
    vlan_file.write(f"vlan {vlan_id}\n")
    vlan_file.write(f"  name vlan_{vlan_id}\n")

vlan_file.close()    



file_data = open("vlan_config_data.conf", "r")
# tempvar = file_data.read()
# print(tempvar)
# print(type(tempvar))

# tempvar2 = file_data.readline()
# print(tempvar2)

tempvar3 = file_data.readlines()
# print(tempvar3)
# print(type(tempvar3))

for item in tempvar3:
    print(item)










# print(file_data.read())
# print(file_data.readline())