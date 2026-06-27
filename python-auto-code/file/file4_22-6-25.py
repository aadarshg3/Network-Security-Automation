intf_config_data_list = [{
    "intf": "Gigabit0/1", 
    "desc": "Connected to server-1",
    "speed": 1000,
    "duplex": "full"
},
{
    "intf": "Gigabit0/2", 
    "desc": "Connected to server-2",
    "speed": 1000,
    "duplex": "full"
},
{
    "intf": "Gigabit0/3", 
    "desc": "Connected to server-3",
    "speed": 1000,
    "duplex": "full"
},
{
    "intf": "Gigabit0/4", 
    "desc": "Connected to server-4",
    "speed": 1000,
    "duplex": "full"
}


]

intf_config_syntax = {
    "intf": "interface {}", 
    "desc": "description {}",
    "speed": "speed {}",
    "duplex": "duplex {}"
}


# for key, value in intf_config_data.items():
#     config = intf_config_syntax[key].format(intf_config_data[key])
#     print(config)

# file1 = open("intended_config.txt", "w") 
with open("intended_config.txt", "w") as file1:
    for intf_config_data in intf_config_data_list:
        # temp = []
        for key in intf_config_data.keys():
            config = intf_config_syntax[key].format(intf_config_data[key])
            # print(config)
            file1.write(config + "\n")

r_file = open("intended_config.txt", "r") 
data1 = r_file.read() # data type is string
r_file.close()

r_file = open("intended_config.txt", "r") 
data2 = r_file.readlines() # data type is list
r_file.close()



print(data1)
print(data2)
# print(data3)





# notes: NAPALM takes input in string
# Netmiko takes input as list 
# 
