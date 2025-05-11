ip = input("Enter your ip: ")

if ip.startswith("10."):
    print("Class A Private IP Address")
elif ip.startswith("172.") and float(ip[4:7]) >= 16. and float(ip[4:7])<= 31.:
    print("Class B Private IP Address")   
elif ip.startswith("192.168."):
    print("Class C Private IP Address")    
else:
    print("Not a Private IP Address")    
    
    
'''
===========================================
################ output ##################
===========================================

root@Aadarshg3:~/devnet/autobundle-may# 
root@Aadarshg3:~/devnet/autobundle-may# python3 private-ip.py 
Enter your ip: 10.2.3.4
Class A Private IP Address
root@Aadarshg3:~/devnet/autobundle-may# python3 private-ip.py 
Enter your ip: 172.16.32.34
Class B Private IP Address
root@Aadarshg3:~/devnet/autobundle-may# python3 private-ip.py 
Enter your ip: 172.160.2.4
Not a Private IP Address
root@Aadarshg3:~/devnet/autobundle-may# python3 private-ip.py 
Enter your ip: 192.168.2.4
Class C Private IP Address
root@Aadarshg3:~/devnet/autobundle-may# 

'''    