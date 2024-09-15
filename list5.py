ip = input("Enter your ip: ")

flag = True

for char in ip:
    # if char.isalpha() or char in "?><!@#$%^&*()?/," :
    if char.isdecimal() != True and char != ".":
        print("Given IP contains char hence not valid")
        # flag = False
        # break
        exit()

    
        
if flag == True:        
    ip = ip.split(".")
    if (float(ip[0]) >= 0 and float(ip[0]) <=255) and (float(ip[1])>=0 and float(ip[1]) <= 255 ) and (float(ip[2]) >= 0 and float(ip[2]) <=255 ) and (float(ip[3]) >= 0 and float(ip[3]) <=255) :
        print("Given IP is Valid wrt octet")
    else:
        print("Given IP is not a Valid wrt octet")    


'''
===============================Sid_SIR-COPY---------------------------


ip = input("Enter your ip:")

flag = True
for char in ip:
    # if char.isalpha() or char in "@#$%^&*()_+<>?,":
    if char.isdecimal() != True:
        print("Given ip is not valid ip")
        flag = False
        break

if flag == True:
    ip = ip.split(".")
    if (int(ip[0]) >=0 and int(ip[0]) <=255) and (int(ip[1]) >=0 and int(ip[1]) <=255) and (int(ip[2]) >=0 and int(ip[2]) <=255) and (int(ip[3]) >=0 and int(ip[3]) <=255):
        print("Given ip is Valid wrt octets")
    else:
        print("Given ip is NOT Valid wrt octets")
        
        
###################------  IP-Validation-1  -----###################        
        

ip = input("Enter your ip: ")

for char in ip:
    if char.isalpha() or char in "?><!@#$%^&*()?/," :
        print("Given IP contains char hence not valid")
        flag = False
        break
    else:
        flag = True
    
        
if flag == True:        
    ip = ip.split(".")
    if (float(ip[0]) >= 0 and float(ip[0]) <=255) and (float(ip[1])>=0 and float(ip[1]) <= 255 ) and (float(ip[2]) >= 0 and float(ip[2]) <=255 ) and (float(ip[3]) >= 0 and float(ip[3]) <=255) :
        print("Given IP is Valid wrt octet")
    else:
        print("Given IP is not a Valid wrt octet")    



'''