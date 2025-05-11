# new_device_inf1 = [
#     { "device_ip": "10.2.3.4", "model": 9800, "site": "site-a", "rack": "rack1", "os_ver": 16.6,
#         "mgmt_ips": ["10.3.3.1", "10.3.3.2"]},
#     { "device_ip": "20.2.3.4", "model": 9500, "site": "site-b", "rack": "rack2", "os_ver": 20.6,
#         "mgmt_ips": ["20.3.3.1", "20.3.3.2"]},
#     { "device_ip": "30.2.3.4", "model": 9300, "site": "site-c", "rack": "rack3", "os_ver": 19.6,
#         "mgmt_ips": ["30.3.3.1", "30.3.3.2"]}
#  ]

# new_device_info2 = {
#     "sw1": { "device_ip": "10.2.3.4", "model": 9800, "site": "site-a", "rack": "rack1", "os_ver": 16.6,
#         "mgmt_ips": ["10.3.3.1", "10.3.3.2"]},
#     "sw2":{ "device_ip": "20.2.3.4", "model": 9500, "site": "site-b", "rack": "rack2", "os_ver": 20.6,
#         "mgmt_ips": ["20.3.3.1", "20.3.3.2"]},
#     "sw3":{ "device_ip": "30.2.3.4", "model": 9300, "site": "site-c", "rack": "rack3", "os_ver": 19.6,
#         "mgmt_ips": ["30.3.3.1", "30.3.3.2"]}
# }



# print(new_device_info2["sw1"]["mgmt_ips"][1])
# print(new_device_info2["sw2"]["mgmt_ips"][0])

new_device_info1 = [
    { "device_ip": "10.2.3.4", "model": 9800, "site": "site-a", "rack": "rack1", "os_ver": 16.6,
        "mgmt_ips": ["10.3.3.1", "10.3.3.2"]},
    { "device_ip": "20.2.3.4", "model": 9500, "site": "site-b", "rack": "rack2", "os_ver": 20.6,
        "mgmt_ips": ["20.3.3.1", "20.3.3.2"]},
    { "device_ip": "30.2.3.4", "model": 9300, "site": "site-c", "rack": "rack3", "os_ver": 19.6,
        "mgmt_ips": ["30.3.3.1", "30.3.3.2"]}
]

sw1 = { "device_ip": "10.2.3.4", "model": 9800, "site": "site-a", "rack": "rack1", "os_ver": 16.6,
        "mgmt_ips": ["10.3.3.1", "10.3.3.2"]}

# print(sw1.items())

# for ankit, pradeep in sw1.items():
#     print(ankit, pradeep)

for data in new_device_info1:
    for k, v in data.items():
        print(k, v)