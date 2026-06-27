
""" 
>>> ip = "10.2.3.4"
>>> newip = ip.split(".")
>>> newip
['10', '2', '3', '4']
>>> 
>>> 
>>> newip[2]
'3'
>>> newip[2].strip()
'3'
>>> dir(list)
['__add__', '__class__', '__class_getitem__', '__contains__', '__delattr__', '__delitem__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getitem__', '__gt__', '__hash__', '__iadd__', '__imul__', '__init__', '__init_subclass__', '__iter__', '__le__', '__len__', '__lt__', '__mul__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__reversed__', '__rmul__', '__setattr__', '__setitem__', '__sizeof__', '__str__', '__subclasshook__', 'append', 'clear', 'copy', 'count', 'extend', 'index', 'insert', 'pop', 'remove', 'reverse', 'sort']
>>> 
>>> 
>>> 
>>> 
>>> ip
'10.2.3.4'
>>> newip
['10', '2', '3', '4']
>>> ".".join(newip)
'10.2.3.4'
>>> newip
['10', '2', '3', '4']
>>> 


"""

""" 
ip = "  10  .2  .3 . 4  "

# Step 1: Split the IP address by the period
segments = ip.split('.')

# Step 2: Strip spaces from each segment
final_ip_list = [segment.strip() for segment in segments]

# Step 3: Join the segments back together with a period
clean_ip = '.'.join(final_ip_list)

print(clean_ip)


"""

"""

ip = input("Enter your ip: ")

# ip = "  10  .2  .3 . 4  "
ip1 = ip.split('.')
# print(ip1)
# print(type(ip1))

final_ip_list = []
# print(type(final_ip_list))

for ele in ip1:
    stripped_segment = ele.strip()
    final_ip_list.append(stripped_segment)
print(final_ip_list)
clean_ip = '.'.join(final_ip_list)
print(clean_ip)    


#================================================================

if final_ip_list[0] == "10." and final_ip_list >= 0 and final_ip_list <=255:
    print("Class A Private IP")
else:
    print("Not an IP")

=============explanation of code above==========>>

We loop through each segment in the segments list.
Inside the loop, ele.strip() removes the leading and trailing spaces.
The stripped segment is then appended to the final_ip_list list.
After this loop, final_ip_list becomes: ['10', '2', '3', '4'].



# print(final_ip_list)

"""


ip1 = input("Enter your ip: ")

# ip = "  10  .2  .3 . 4  "
ip2 = ip1.split('.')
# print(ip2)
# print(type(ip2))

final_ip_list = []
# print(type(final_ip_list))

for ele in ip2:
    stripped_segment = ele.strip()
    final_ip_list.append(stripped_segment)
print(final_ip_list)
ip = '.'.join(final_ip_list)
print(ip)   

#---------Code_Here---------------------

ip3 = input("Enter your ip: ")

if ip3.startswith("10."):
    print("Class A Private IP Address")
elif ip3.startswith("172.") and float(ip[4:7]) >= 16. and float(ip[4:7])<= 31.:
    print("Class B Private IP Address")   
elif ip3.startswith("192.168."):
    print("Class C Private IP Address")    
else:
    print("Not a Private IP Address")        

    
    

