print("Enter your ip")
ip = input()

# ip = input("Enter your ip: ")

if ip.startswith("10."):
    print("Class A Private IP Address")
elif ip.startswith("172.") and float(ip[4:7]) >= 16. and float(ip[4:7])<= 31.:
    print("Class B Private IP Address")   
elif ip.startswith("192.168."):
    print("Class C Private IP Address")    
else:
    print("Not a Private IP Address")  
