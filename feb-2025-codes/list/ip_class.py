ip = input("Enter your IP address:")
# print(type(len(ip)))

ip = ip.split('.')
# print(ip)
# print(len(ip))

if len(ip) == 4:
    # print("Keep working")
    status = True
    for octet in ip:
        if octet.strip().isnumeric() and (int(octet) >=0 and int(octet) <=255):
            # status = True # Not required
            pass
            # print("Octet is valid") # Not required
            
        else:
            print("IP NOT VALID - Make sure each octet is numeric and between 0 - 255")
            status = False
            break
    print(status)
    if status == True:
        if float(ip[0]) == 10.0:
            print("Class A Private IP")
        elif int(ip[0]) == 172 and int(ip[1]) >= 16 and int(ip[1]) <= 31:
            print("Class B")
        elif  int(ip[0]) == 192 and int(ip[1]) == 168:
            print("Class C")
        else:
            print("Not Valid ip")
        
else:
    print("Not valid ip - Ip is not having 4 octets")


