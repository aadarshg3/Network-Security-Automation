"""
>>> vlan_id = 10
>>> vlan_command = "vlan {}"
>>> vlan_command.format(vlan_id)
'vlan 10'
>>> 
>>> 
>>> "vlan{}".format(10)
'vlan10'
>>> 
>>>  

"""


""" 
vlan_id = input("Enter vlan id: ")
vlan_command = "vlan {}"
vlan_conf = vlan_command.format(vlan_id)
print(vlan_conf)

"""

""" 
vlan_command = "vlan {}"
vlan_conf = vlan_command.format(vlan_id)
print(vlan_conf)

# =========================Example of Data-Type-Casting =======================

>>> vlan_id = input("Enter vlan id: ")
Enter vlan id: 10
>>> vlan_command = "vlan {}"
>>> vlan_conf = vlan_command.format(vlan_id)
>>> print(vlan_conf)
vlan 10
>>> 
>>> 
>>> vlan_id 
'10'
>>> vlan_id + 10
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: can only concatenate str (not "int") to str
>>> 
>>> "20" + 20
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: can only concatenate str (not "int") to str
>>> 
>>> int("20") + 20
40
>>> 
>>> "20" + str(20)
'2020'
>>> 
>>> 
>>> vlan_id + "10"
'1010'
>>> 
>>> 


# vlan_id = input("Enter vlan id: ")
# vlan_command = "vlan {}"
# vlan_conf = vlan_command.format(vlan_id)
# print(vlan_conf)

# ===========================End of Data-Type-Casting===================

"""
# =========================== "F string Example" ===================

usr_name = input("Enter username: ")
pwd = input ("Enter password")
# # user_config = "username {} password {}".format(usr_name, pwd)
# print(user_config)


# user_config = "username" + " " + usr_name + " " + "passwrd" + " " + pwd
# print(user_config)

# =============== "F String example" ==============================

user_config = f"username {usr_name} password {pwd}"
print(user_config)


# traceroute destip source intf 

# =================Code of Tracert =========================

# dst_ip = input("Enter destination IP: ")
# intf = input("Enter interface name:")
# traceroute_config = "traceroute {} interface {}".format(dst_ip, intf)
# print(traceroute_config)

""" 
# ==================== output of traceroute command =========================
root@Aadarshg3:~/devnet/autobundle-may# 
root@Aadarshg3:~/devnet/autobundle-may# python3 string3_June2nd.py 
Enter destination IP: 8.8.8.8
Enter interface name:Gi1/1
traceroute 8.8.8.8 interface Gi1/1

==================== End of traceroute command =========================
"""
 
# ============= config of vlan configuration ====================


# vlan_id = input("Enter your vlan id: ")
# vlan_config = "vlan {}".format(vlan_id)
# print(vlan_config)


# ================== output of vlan config =====================
""" 
root@Aadarshg3:~/devnet/autobundle-may# python3 string3_June2nd.py 
Enter your vlan id: 10
vlan 10
root@Aadarshg3:~/devnet/autobundle-may# 

"""








