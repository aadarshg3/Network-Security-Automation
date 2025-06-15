import time
from datetime import datetime

# # reading from txt file
# myfile = open("vlan_data.txt", "r")
# data = myfile.readlines()
# # print(myfile.readlines())
# # print(data[0:1])

# for item in data:
#     print(item.strip("\n"))
# myfile.close()    



# myfile = open(f"vlan_data{datetime.now()}.txt", "w", newline='\n')
# p_data = "This is Aadarsh from NetGIndia"
# myfile.write(p_data)
# myfile.close()

with open("vlan_data.txt", "a") as myfile:
    data = myfile.read()
    data = myfile.readlines()
    # data = myfile.readline()
    print(data)