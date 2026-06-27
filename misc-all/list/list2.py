
































'''
root@Aadarshg3:~/devnet/autobundle-may# python3
Python 3.10.12 (main, Jun 11 2023, 05:26:28) [GCC 11.4.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> 
>>> 
>>> list = ['R1', 'R2', 'R3']
>>> list[1]
'R2'
>>> list[0]
'R1'
>>> 
>>> 
>>> list2 = ['R1', '10.4', ['R2', 10.5]]
>>> list2[0]
'R1'
>>> list2[2][0]
'R2'
>>> listoflist = [[1,2,3], [4,5,6], [7,8,0]]
>>> listoflist[0]
[1, 2, 3]
>>> listoflist[1]
[4, 5, 6]
>>> listoflist[2]
[7, 8, 0]
>>> 
>>> 
>>> 
>>> 
>>> listoflist[1]
[4, 5, 6]
>>> listoflist[0]
[1, 2, 3]
>>> listoflist[0][1]
2
>>> temp = listoflist[0]
>>> type(temp)
<class 'list'>
>>> temp[1]
2
>>> 
>>> 
>>> 
>>> 
>>> 
>>> 
>>> 
>>> templist =  ["router", 16.6]
>>> temp[0][1]
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: 'int' object is not subscriptable
>>> temp[0][2]
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: 'int' object is not subscriptable
>>> templist =  ["router", 16.6]
>>> 
>>> 
>>> 
>>> templist[0]
'router'
>>> templist[0][1]
'o'
>>> templist[0][1]
'o'
>>> 
>>> 
>>> 
>>> templist =  ["router", 16.6]
>>> templist[0][1]
'o'
>>> len(templist[0][1])
1
>>> len(templist)
2
>>> len(templist[0])
6
>>> len(templist[1])
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: object of type 'float' has no len()
>>> templist[1]
16.6
>>> templist[1][1]
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: 'float' object is not subscriptable
>>> templist =  ["router", 16.6, 123]
>>> templist[2][1]
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: 'int' object is not subscriptable
>>> 
>>> 
>>> 
>>> string1 = "Router"
>>> string1[0]
'R'
>>> string1[0][1]
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
IndexError: string index out of range
>>> string1[0]
'R'
>>> string1[2]
'u'
>>> string1[1]
'o'
>>> listoflist = [[[10,20,30], [40,50,60], [70,80,90]],[4,5,6], [7,8,9]] 
>>> listoflist[1][1]
5
>>> listoflist[0][1][1]
50
>>> listoflist[2][2]
9
>>> listoflist[1,2,3,4,5]
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: list indices must be integers or slices, not tuple
>>> listoflist = [1,2,3,4,5]
>>> listoflist[::-1]
[5, 4, 3, 2, 1]
>>> listoflist[0]
1
>>> listoflist[0:2]
[1, 2]
>>> listoflist[0:2]
[1, 2]
>>> listoflist[::-1]
[5, 4, 3, 2, 1]
>>> 
>>> 
>>> 
>>> 
>>> listoflist = [1,2,3,4,5]
>>> listoflist = [1,2,3,4,5]
>>> 
>>> 
>>> 
>>> ip_list = ["10.2.3.4", "11.4.56.6", "12.23.45.67", "172.16.2.3"]
>>> 
>>> 
>>> for item in ip_list:
...     print(item)
... 
10.2.3.4
11.4.56.6
12.23.45.67
172.16.2.3
>>> 
>>> for item in ip_list:
...     print("Connecting to device" , item)
... 
Connecting to device 10.2.3.4
Connecting to device 11.4.56.6
Connecting to device 12.23.45.67
Connecting to device 172.16.2.3
>>> for item in ip_list:
...     print("configuring" , item)
... 
configuring 10.2.3.4
configuring 11.4.56.6
configuring 12.23.45.67
configuring 172.16.2.3
>>> ip_list = ["10.2.3.4", "11.4.56.6", "12.23.45.67", "172.16.2.3"]
>>> 
>>> 
>>> 
>>> 
>>> 
>>> ip_list = ["10.2.3.4", "11.4.56.6", "12.23.45.67", "172.16.2.3"]
>>> 
>>> 
>>> 
>>> config_set = ["conf t", "interface ge0/1", "switchport mode access", "switchport access vlan 10"]
>>> 
>>> 
>>> for item in config_set:
...     print("configuring vlan", item)
... 
configuring vlan conf t
configuring vlan interface ge0/1
configuring vlan switchport mode access
configuring vlan switchport access vlan 10
>>> 
>>> 
>>> 
>>> config_set = ["conf t", "interface ge0/1", "switchport mode access", "switchport access vlan 10"]
>>>     print(item)
  File "<stdin>", line 1
    print(item)
IndentationError: unexpected indent
>>> 
>>> 
>>> config_set = ["conf t", "interface ge0/1", "switchport mode access", "switchport access vlan 10"]
>>> for item in config_set:
...     print(item)
... 
conf t
interface ge0/1
switchport mode access
switchport access vlan 10
>>> 
>>> 
>>> 
>>> 
>>> 
>>> for item in listoflist:
...     print(item)
... 
1
2
3
4
5
>>> listoflist = [[[10,20,30], [40,50,60], [70,80,90]],[4,5,6], [7,8,9]]
>>> for item in listoflist:
...     print(item)
... 
[[10, 20, 30], [40, 50, 60], [70, 80, 90]]
[4, 5, 6]
[7, 8, 9]
>>> 
>>> 
>>> 
>>> for item in listoflist:
...     print(item)
...     for ele in item:
...             print(ele)
... 
[[10, 20, 30], [40, 50, 60], [70, 80, 90]]
[10, 20, 30]
[40, 50, 60]
[70, 80, 90]
[4, 5, 6]
4
5
6
[7, 8, 9]
7
8
9
>>> for item in listoflist:
...     print(item)
... 
[[10, 20, 30], [40, 50, 60], [70, 80, 90]]
[4, 5, 6]
[7, 8, 9]
>>> for item in listoflist:
...     print(item)
...     for ele in item:
...     print(item)
  File "<stdin>", line 4
    print(item)
    ^
IndentationError: expected an indented block after 'for' statement on line 3
>>> for item in listoflist:
...     print(item)
...     for ele in item:
...             print(ele)
... 
[[10, 20, 30], [40, 50, 60], [70, 80, 90]]
[10, 20, 30]
[40, 50, 60]
[70, 80, 90]
[4, 5, 6]
4
5
6
[7, 8, 9]
7
8
9
>>> 
>>> 
>>> 
>>> 
>>> 
>>> 
>>> listpflist = [[[1,2,3],[4,5,6],[7,8,9]], [[10,20,30],[40,50,60], [100,200,300]]]
>>> for item in listpflist:
...     for ele1 in item:
...             for ele2 in ele1:
...                     print(ele2)
... 
1
2
3
4
5
6
7
8
9
10
20
30
40
50
60
100
200
300
>>> 
>>> 

Adding this to GIT

'''