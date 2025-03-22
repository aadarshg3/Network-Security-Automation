# code for ip octet validation

def ip_octet_validation(ip):
    for char in ip:
        if char.isalpha() or char in "@#$%^&*()_+<>?,":
            message = "Given ip is not valid ip"
            flag = True
            break
        else:
            flag = False

    if flag == False:
        ip = ip.split(".")
        if (int(ip[0]) >=0 and int(ip[0]) <=255) and (int(ip[1]) >=0 and int(ip[1]) <=255) and (int(ip[2]) >=0 and int(ip[2]) <=255) and (int(ip[3]) >=0 and int(ip[3]) <=255):
            message = "Given ip is Valid wrt octets"
        else:
            message = "Given ip is NOT Valid wrt octets"
            
    return message

while True:
    ip = input("Enter your ip:")
    msg = ip_octet_validation(ip)
    print(msg)
    choice = input("Do you want continue? Y/N")
    if choice == "N":
        break
    elif choice == "Y": 
        continue

