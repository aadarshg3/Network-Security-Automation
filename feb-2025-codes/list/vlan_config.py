
site_list = ["Sydney", "Delhi", "Bangaluru"]
device_ip = ["10.2.3.4", "192.168.1.0", "172.16.6.7"]
vlans = [10, 30, 100, 200, 250]



for site in site_list:
    print("configuring", site)
    for ip in device_ip:
        print("Configuring ", ip)
        for vlan in vlans:
            # if vlan in [30, 200]:
            if vlan == 30 or vlan == 200:
                print("vlan",  vlan)
                print(" name", "vlan_" + str(vlan))
    