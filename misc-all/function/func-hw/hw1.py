def ospf_conf(process_id, device_list, area_id, network_info):
    for i in range(len(device_list)):
        print(f'device: {device_list[i]}')
        print(f"router ospf {process_id[i]}")
        for n,w in network_info[i].items():
            print(f"network {n} {w} area {area_id[i]}")    



process_id = ["100", "200", "300"]
device_list = ["R1", "R2", "R3"]

network_info = [
    {"10.1.1.0": "0.0.0.255"},
    {"20.1.1.0": "0.0.3.255"},
    {"12.1.1.0": "0.0.0.31"}
]

area_id = ["0", "1", "5"]

ospf_conf(process_id, device_list, area_id, network_info)





""" 
process_id = ["100", "200", "300"]
device_list = ["R1", "R2", "R3"]

network_info = [
    {"10.1.1.0": "0.0.0.255"},
    {"20.1.1.0": "0.0.3.255"},
    {"12.1.1.0": "0.0.0.31"}
]

area_id = ["0", "1", "5"]

# write a code for 1 router to 
# configure OSPF with 3 process-ids


for i in range(len(device_list)):
    print(f'device: {device_list[i]}')
    print(f"router ospf {process_id[i]}")
    for n,w in network_info[i].items():
        print(f"network {n} {w} area {area_id[i]}")

 """





# ip_addr = [
#     {"ip1": "10.1.1.0"},
#     {"ip2": "20.1.1.0" },
#     {"ip3": "12.1.1.0"}
# ]

# wild_mask = [
#     {"wm1": "0.0.0.255"},
#     {"wm2": "0.0.3.255"},
#     {"wm3": "0.0.0.31"}
# ]


"""

process_id = ["100", "200", "300"]
device_list = ["R1", "R2", "R3"]
network_info = [
    {"10.1.1.0": "0.0.0.255"},
    {"20.1.1.0": "0.0.3.255"},
    {"12.1.1.0": "0.0.0.31"}
]
area_id = ["0", "1", "5"]

# Generate and print OSPF configuration
for i in range(len(device_list)):
    print(f"Device: {device_list[i]}")
    print(f"router ospf {process_id[i]}")
    for network, wildcard in network_info[i].items():
        print(f" network {network} {wildcard} area {area_id[i]}")
    print("-" * 30)


"""


