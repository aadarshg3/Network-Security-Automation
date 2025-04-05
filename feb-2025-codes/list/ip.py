# - take ip as an input from user
# - check if it has 4 octets
# - check if each octet has value between 0-255
# - find the class of a given ip.

while(True):
    ip = input("Enter your ip:")

    ip = ip.split('.')

    if len(ip) != 4:
        print("IP NOT VALID-1. Enter valid ip")
        continue
    
    for octet in ip:
        if octet.isnumeric():
            octet = int(octet.strip())
        else:
            print("IP NOT VALID-2. Enter valid ip")
            continue
        if octet < 0 or octet > 255:
            print("IP NOT VALID-3. Enter valid ip")
            continue
    
    
    netg@DESKTOP-EBH0I8A:~/devnet$ python3
Python 3.10.12 (main, Jul 29 2024, 16:56:48) [GCC 11.4.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> 
>>> 
>>> 
>>> 
>>> 
>>> devices = []
>>> 
>>> type(device)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
NameError: name 'device' is not defined. Did you mean: 'devices'?
>>> 
>>> type(devices)
<class 'list'>
>>> 
>>> 
>>> 
>>> devices = ["R1", "R2", "R3"]
>>> 
>>> devices = ["R1", "R2", "R3", "R4", "R5"]
>>> 
>>> devices
['R1', 'R2', 'R3', 'R4', 'R5']
>>> 
>>> 
>>> devices[0]
'R1'
>>> devices[1]
'R2'
>>> devices[3]
'R4'
>>> devices[4]
'R5'
>>> devices[5]
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
IndexError: list index out of range
>>> 
>>> 
>>> device_info = ["R1", "Cisco", 10, 16.5]
>>> 
>>> device_info[0]
'R1'
>>> device_info[1]
'Cisco'
>>> device_info[2]
10
>>> device_info[3]
16.5
>>> device_info[4]
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
IndexError: list index out of range
>>> 
>>> device_info[1]
'Cisco'
>>> 
>>> 
>>> 
>>> 
>>> device_info[1][0]
'C'
>>> device_info[1][1]
'i'
>>> device_info[1][1]
'i'
>>> 
>>> device_info[1][0:2]
'Ci'
>>> 
>>> device_info
['R1', 'Cisco', 10, 16.5]
>>> 
>>> device_info[0:2]
['R1', 'Cisco']
>>> 
>>> device_info[1:3]
['Cisco', 10]
>>> 
>>> 
>>> 
>>> device_info[::-1]
[16.5, 10, 'Cisco', 'R1']
>>> 
>>> 
>>> device_info
['R1', 'Cisco', 10, 16.5]
>>> 
>>> dir(list)
['__add__', '__class__', '__class_getitem__', '__contains__', '__delattr__', '__delitem__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getitem__', '__gt__', '__hash__', '__iadd__', '__imul__', '__init__', '__init_subclass__', '__iter__', '__le__', '__len__', '__lt__', '__mul__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__reversed__', '__rmul__', '__setattr__', '__setitem__', '__sizeof__', '__str__', '__subclasshook__', 'append', 'clear', 'copy', 'count', 'extend', 'index', 'insert', 'pop', 'remove', 'reverse', 'sort']
>>> 
>>> dir(device_info)
['__add__', '__class__', '__class_getitem__', '__contains__', '__delattr__', '__delitem__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getitem__', '__gt__', '__hash__', '__iadd__', '__imul__', '__init__', '__init_subclass__', '__iter__', '__le__', '__len__', '__lt__', '__mul__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__reversed__', '__rmul__', '__setattr__', '__setitem__', '__sizeof__', '__str__', '__subclasshook__', 'append', 'clear', 'copy', 'count', 'extend', 'index', 'insert', 'pop', 'remove', 'reverse', 'sort']
>>> 
>>> 
>>> dir(str)
['__add__', '__class__', '__contains__', '__delattr__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getitem__', '__getnewargs__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__iter__', '__le__', '__len__', '__lt__', '__mod__', '__mul__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__rmod__', '__rmul__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', 'capitalize', 'casefold', 'center', 'count', 'encode', 'endswith', 'expandtabs', 'find', 'format', 'format_map', 'index', 'isalnum', 'isalpha', 'isascii', 'isdecimal', 'isdigit', 'isidentifier', 'islower', 'isnumeric', 'isprintable', 'isspace', 'istitle', 'isupper', 'join', 'ljust', 'lower', 'lstrip', 'maketrans', 'partition', 'removeprefix', 'removesuffix', 'replace', 'rfind', 'rindex', 'rjust', 'rpartition', 'rsplit', 'rstrip', 'split', 'splitlines', 'startswith', 'strip', 'swapcase', 'title', 'translate', 'upper', 'zfill']
>>> 
>>> o/p = 10
  File "<stdin>", line 1
    o/p = 10
    ^^^
SyntaxError: cannot assign to expression here. Maybe you meant '==' instead of '='?
>>> 
>>> help(list.insert)

>>> help(list.index)

>>> 
>>> 
>>> 
>>> device_info = ["R1", "Cisco", 10, 16.5]
>>> 
>>> 
>>> device_info[1]
'Cisco'
>>> 
>>> for item in device_info:
...     print(item)
... 
R1
Cisco
10
16.5
>>> 
>>> for item in device_info:
...     if item == "Cisco":
...             print("Vendor is Cisco")
... 
Vendor is Cisco
>>> 
>>> 
>>> 
>>> devices = ["R1", "R2", "R3", "R4"]
>>> 
>>> for item in device_info:
... 
KeyboardInterrupt
>>> 
>>> 
>>> for item in devices:
...     print(item)
... 
R1
R2
R3
R4
>>> 