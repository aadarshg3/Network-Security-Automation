vlan_id = [10, 20, 30, 40]
os_version = ["ios-15.5", "ios-15,6" , "ios-16.6"]

device_list = ["R1", "R2", "R3" , "R4"]
device_info = ["switch", 10, 15.5 , "24-8-2025", "cisco"]

for item in device_info:
    print(item)
    
    
    
    

"""
root@Aadarshg3:~/devnet/autobundle-may# python3 list1.py 
switch
10
15.5
24-8-2025
cisco
root@Aadarshg3:~/devnet/autobundle-may# 

"""

"""
root@Aadarshg3:~/devnet# python3
Python 3.10.12 (main, Jun 11 2023, 05:26:28) [GCC 11.4.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> device_list = ["R1", "R2", "R3" , "R4"]
>>> vlan_id = [10, 20, 30, 40]
>>> os_version = ["ios-15.5", "ios-15,6" , "ios-16.6"]
>>> 
>>> device_list = ["R1", "R2", "R3" , "R4"]
>>> device_info = ["switch", 10, 15.5 , "24-8-2025", "cisco"]
>>> device_info[0]
'switch'
>>> device_info[1]
10
>>> device_info[2]
15.5
>>> device_info[2:1]
[]
>>> device_info[2:5]
[15.5, '24-8-2025', 'cisco']
>>> device_info[0]
'switch'
>>> device_info[0:3]
['switch', 10, 15.5]
>>> device_info[-1]
'cisco'
>>> device_info[-1:1]
[]
>>> device_info[-1:5]
['cisco']
>>> device_info[-5]
'switch'
>>> device_info
['switch', 10, 15.5, '24-8-2025', 'cisco']
>>> 
>>> 
>>> device_info[-2:-1]
['24-8-2025']
>>> device_info[-2:0]
[]
>>> device_info[-3:-1]
[15.5, '24-8-2025']
>>> device_info[:-1]
['switch', 10, 15.5, '24-8-2025']
>>> device_info[::-1]
['cisco', '24-8-2025', 15.5, 10, 'switch']
>>> device_info[::1]
['switch', 10, 15.5, '24-8-2025', 'cisco']
>>> 
>>> 
>>> device_info[:]
['switch', 10, 15.5, '24-8-2025', 'cisco']
>>> device_info[::]
['switch', 10, 15.5, '24-8-2025', 'cisco']
>>> 
>>> device_info[::-1]
['cisco', '24-8-2025', 15.5, 10, 'switch']
>>> 
>>> 



==========================================

>>> newlist = []
>>> newlist.append("Router")
>>> newlist
['Router']
>>> newlist.append("switch" , 1)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: list.append() takes exactly one argument (2 given)
>>> )
  File "<stdin>", line 1
    )
    ^
SyntaxError: unmatched ')'
>>> 
>>> 
>>> 
>>> 
>>> newlist
['Router']
>>> newlist.insert(1, "Switch")
>>> newlist
['Router', 'Switch']
>>> newlist.insert(1, "FW")
>>> newlist
['Router', 'FW', 'Switch']
>>> newlist.insert("LB")
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: insert expected 2 arguments, got 1
>>> newlist.append("LB")
>>> 
>>> 
>>> newlist
['Router', 'FW', 'Switch', 'LB']
>>> 

"""