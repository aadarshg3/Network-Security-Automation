# code for private ip validation

def ip_validation(ip2):
    # ip1 = input("Enter your IP address: ")
    ip2 = ip1.split(".")
    # print(ip2)
    # for ele in ip2:
        # print(ele)
    if float(ip2[0]) == 10. and float(ip2[0]) >= 0 and float(ip2[0])<=255 and float(ip2[1])>=0 and float(ip2[1]) <= 255 and float(ip2[2]) >= 0 and float(ip2[2]) <=255 and float(ip2[3]) >= 0 and float(ip2[3]) <=255:
        message = "Class A Private IP Address"
    elif float(ip2[0]) == 172. and float(ip2[1]) >= 16. and float(ip2[1]) <=31. and float(ip2[0]) >= 0 and float(ip2[0])<=255 and float(ip2[1])>=0 and float(ip2[1]) <= 255 and float(ip2[2]) >= 0 and float(ip2[2]) <=255 and float(ip2[3]) >= 0 and float(ip2[3]) <=255: 
        message = "Class B Private IP Address"    
    elif  float(ip2[0]) == 192. and float(ip2[1]) == 168. and float(ip2[0]) >= 0 and float(ip2[0])<=255 and float(ip2[1])>=0 and float(ip2[1]) <= 255 and float(ip2[2]) >= 0 and float(ip2[2]) <=255 and float(ip2[3]) >= 0 and float(ip2[3]) <=255:    
        message = "Class C Private IP Address"
    else:
        message = "Not a Private IP Address"
    
    return message     
        

    
while True:        
    ip1 = input("Enter your IP: ")
    msg = ip_validation(ip1)    
    print(msg)
    choice = input("Do you want to contunue: Y/N ::  ")
    if choice == "N":
        break


    