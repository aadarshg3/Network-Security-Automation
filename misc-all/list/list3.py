ip1 = input("Enter your IP address: ")
ip2 = ip1.split(".")
# print(ip2)
for ele in ip2:
    if ele >= 0 and ele <= 255:
        continue
    if float(ip2[0]) == 10.:
        print("Class A Private IP Address")
    elif float(ip2[0]) == 172. and float(ip2[1]) >= 16. and float(ip2[1]) <=31. :
        print("Class B Private IP Address")     
    elif  float(ip2[0]) == 192. and float(ip2[1]) == 168. :   
        print("Class C Private IP Address")
    else:
        print("Not a Private IP Address")    
    
    
    
    
"""
##### OUTPUT ###########
root@Aadarshg3:~/devnet/autobundle-may# vim list3.py
root@Aadarshg3:~/devnet/autobundle-may# python3 list3.py 
Enter your IP address: 172.16.1.2
['172', '16', '1', '2']
root@Aadarshg3:~/devnet/autobundle-may# python3 list3.py 
Enter your IP address: 10.3.4.5
root@Aadarshg3:~/devnet/autobundle-may# python3 list3.py 
Enter your IP address: 10.3.4.5
root@Aadarshg3:~/devnet/autobundle-may# python3 list3.py 
Enter your IP address: 10.2.3.4
Class A Private IP Address
root@Aadarshg3:~/devnet/autobundle-may# python3 list3.py 
Enter your IP address: 10.1.1.2
Class A Private IP Address
root@Aadarshg3:~/devnet/autobundle-may# python3 list3.py 
Enter your IP address: 172.16.2.3
Class B Private IP Address
root@Aadarshg3:~/devnet/autobundle-may# python3 list3.py 
Enter your IP address: 172.30.4.5
Class B Private IP Address
root@Aadarshg3:~/devnet/autobundle-may# python3 list3.py 
Enter your IP address: 172.56.1.2
root@Aadarshg3:~/devnet/autobundle-may# 
root@Aadarshg3:~/devnet/autobundle-may# 
root@Aadarshg3:~/devnet/autobundle-may# python3 list3.py 
Enter your IP address: 192.168.2.3
Class C Private IP Address
root@Aadarshg3:~/devnet/autobundle-may# python3 list3.py 
Enter your IP address: 192.67.1.2
Not a Private IP Address
root@Aadarshg3:~/devnet/autobundle-may# 
root@Aadarshg3:~/devnet/autobundle-may# 
root@Aadarshg3:~/devnet/autobundle-may# 
root@Aadarshg3:~/devnet/autobundle-may# 




"""    