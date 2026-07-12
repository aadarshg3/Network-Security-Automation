def myfunct1(new_device_info1):
    for data in new_device_info1:
        for k, v in data.items():
            print(k, v)
    # return data
            
            
new_device_info1 = [
    { "device_ip": "10.2.3.4", "model": 9800, "site": "site-a", "rack": "rack1", "os_ver": 16.6,
        "mgmt_ips": ["10.3.3.1", "10.3.3.2"]},
    { "device_ip": "20.2.3.4", "model": 9500, "site": "site-b", "rack": "rack2", "os_ver": 20.6,
        "mgmt_ips": ["20.3.3.1", "20.3.3.2"]},
    { "device_ip": "30.2.3.4", "model": 9300, "site": "site-c", "rack": "rack3", "os_ver": 19.6,
        "mgmt_ips": ["30.3.3.1", "30.3.3.2"]}
]




output = myfunct1(new_device_info1)
print(output)