def eigrp_conf(network_info, device_list, AS_num):
    for i in range(len(device_list)):
        print(f"device: {device_list[i]}")
        print(f"router eigrp {AS_num[i]}")
        for net,wild in network_info[i].items():
            print(f"network {net} {wild}")
        print("network 0.0.0.0 0.0.0.0")

network_info = [
    {"10.1.1.0": "0.0.0.255"},
    {"20.1.1.0": "0.0.3.255"},
    {"12.1.1.0": "0.0.0.31"}
]

device_list = ["R1", "R2", "R3"]

AS_num = [100, 200, 300]


eigrp_conf(network_info, device_list, AS_num)





""" 
network_info = [
    {"10.1.1.0": "0.0.0.255"},
    {"20.1.1.0": "0.0.3.255"},
    {"12.1.1.0": "0.0.0.31"}
]

device_list = ["R1", "R2", "R3"]

AS_num = [100, 200, 300]

for i in range(len(device_list)):
    print(f"device: {device_list[i]}")
    print(f"router eigrp {AS_num[i]}")
    for net,wild in network_info[i].items():
        print(f"network {net} {wild}")
    print("network 0.0.0.0 0.0.0.0")

"""


"""

network_info = [
    {"10.1.1.0": "0.0.0.255"},
    {"20.1.1.0": "0.0.3.255"},
    {"12.1.1.0": "0.0.0.31"}
]

device_list = ["R1", "R2", "R3"]

AS_num = [100, 200, 300]

for device, as_num, networks in zip(device_list, AS_num, network_info):
    print(f"device: {device}")
    print(f"router eigrp {as_num}")
    for net, wild in networks.items():
        print(f"network {net} {wild}")
    print("network 0.0.0.0 0.0.0.0")


"""