root@Aadarshg3:~/devnet# 
root@Aadarshg3:~/devnet# 
root@Aadarshg3:~/devnet# 
root@Aadarshg3:~/devnet# ifconfig
eth1: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 192.168.129.1  netmask 255.255.255.0  broadcast 192.168.129.255
        inet6 fe80::cbe7:9b1f:1d1:5d87  prefixlen 64  scopeid 0xfd<compat,link,site,host>
        ether 00:50:56:c0:00:01  (Ethernet)
        RX packets 0  bytes 0 (0.0 B)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 0  bytes 0 (0.0 B)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

eth2: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.1.1.1  netmask 255.255.255.0  broadcast 10.1.1.255
        inet6 fe80::8b3b:9b1:5552:47b8  prefixlen 64  scopeid 0xfd<compat,link,site,host>
        ether 00:50:56:c0:00:02  (Ethernet)
        RX packets 0  bytes 0 (0.0 B)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 0  bytes 0 (0.0 B)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

eth3: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 172.16.1.1  netmask 255.255.255.0  broadcast 172.16.1.255
        inet6 fe80::40e5:fe87:7122:1565  prefixlen 64  scopeid 0xfd<compat,link,site,host>
        ether 00:50:56:c0:00:03  (Ethernet)
        RX packets 0  bytes 0 (0.0 B)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 0  bytes 0 (0.0 B)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

eth4: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 192.168.146.1  netmask 255.255.255.0  broadcast 192.168.146.255
        inet6 fe80::d043:4a4c:929b:2617  prefixlen 64  scopeid 0xfd<compat,link,site,host>
        ether 00:50:56:c0:00:08  (Ethernet)
        RX packets 0  bytes 0 (0.0 B)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 0  bytes 0 (0.0 B)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 1500
        inet 127.0.0.1  netmask 255.0.0.0
        inet6 ::1  prefixlen 128  scopeid 0xfe<compat,link,site,host>
        loop  (Local Loopback)
        RX packets 0  bytes 0 (0.0 B)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 0  bytes 0 (0.0 B)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

wifi0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 192.168.1.5  netmask 255.255.255.0  broadcast 192.168.1.255
        inet6 fe80::1768:d7c7:d024:9021  prefixlen 64  scopeid 0xfd<compat,link,site,host>
        ether b4:b5:b6:a8:22:85  (Ethernet)
        RX packets 0  bytes 0 (0.0 B)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 0  bytes 0 (0.0 B)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

wifi2: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 192.168.137.1  netmask 255.255.255.0  broadcast 192.168.137.255
        inet6 fe80::55bc:7ed7:5a90:c7dd  prefixlen 64  scopeid 0xfd<compat,link,site,host>
        ether b6:b5:b6:a8:22:b5  (Ethernet)
        RX packets 0  bytes 0 (0.0 B)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 0  bytes 0 (0.0 B)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

root@Aadarshg3:~/devnet# python3
Python 3.10.12 (main, Jun 11 2023, 05:26:28) [GCC 11.4.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> b = "Hello, World!"
>>> print(b[:5])
Hello
>>> b = "Hello, World!"
>>> print(b[2:])
llo, World!
>>> a = " Hello, World! "
>>> print(a.strip()) # returns "Hello, World!"
Hello, World!
>>> a = "Hello, World!"
>>> print(a.split(",")) # returns ['Hello', ' World!']
['Hello', ' World!']
>>> a = "Hello"
>>> b = "World"
>>> c = a + b
>>> print(c)
HelloWorld
>>> a = "Hello"
>>> b = "World"
>>> c = a + " " + b
>>> print(c)
Hello World
>>> price = 59
>>> txt = f"The price is {price:.2f} dollars"
>>> print(txt)
The price is 59.00 dollars
>>> txt = f"The price is {20 * 59} dollars"
>>> print(txt)
The price is 1180 dollars
>>> txt = "We are the so-called "Vikings" from the north."
  File "<stdin>", line 1
    txt = "We are the so-called "Vikings" from the north."
                                 ^^^^^^^
SyntaxError: invalid syntax
>>> txt = "We are the so-called \"Vikings\" from the north."
>>> print(txt)
We are the so-called "Vikings" from the north.
>>> txt = "hello, and welcome to my world."
>>> 
>>> x = txt.capitalize()
>>> 
>>> print (x)
Hello, and welcome to my world.
>>> x
'Hello, and welcome to my world.'
>>> x = txt.capitalize()
>>> print (x)
Hello, and welcome to my world.
>>> txt = "python is FUN!"
>>> 
>>> x = txt.capitalize()
>>> 
>>> print (x)
Python is fun!
>>> txt = "36 is my age."
>>> 
>>> x = txt.capitalize()
>>> 
>>> print (x)
36 is my age.
>>> txt = "Hello, And Welcome To My World!"
>>> 
>>> x = txt.casefold()
>>> 
>>> print(x)
hello, and welcome to my world!
>>> txt = "banana"
>>> 
>>> x = txt.center(20)
>>> 
>>> print(x)
       banana       
>>> txt = "banana"
>>> 
>>> x = txt.center(20, "O")
>>> 
>>> print(x)
OOOOOOObananaOOOOOOO
>>> txt = "I love apples, apple are my favorite fruit"
>>> 
>>> x = txt.count("apple")
>>> 
>>> print(x)
2
>>> txt = "I love apples, apple are my favorite fruit"
>>> 
>>> x = txt.count("apple", 10, 24)
>>> 
>>> print(x)
1
>>> txt = "Hello, welcome to my world."
>>> 
>>> x = txt.endswith(".")
>>> 
>>> print(x)
True
>>> txt = "Hello, welcome to my world."
>>> 
>>> x = txt.endswith("my world.")
>>> 
>>> print(x)
True
>>> txt = "Hello, welcome to my world."
>>> 
>>> x = txt.endswith("my world.", 5, 11)
>>> 
>>> print(x)
False
>>> txt = "H\te\tl\tl\to"
>>> 
>>> print(txt)
H       e       l       l       o
>>> print(txt.expandtabs())
H       e       l       l       o
>>> print(txt.expandtabs(2))
H e l l o
>>> print(txt.expandtabs(4))
H   e   l   l   o
>>> print(txt.expandtabs(10))
H         e         l         l         o
>>> txt = "Hello, welcome to my world."
>>> 
>>> x = txt.find("e")
>>> 
>>> print(x)
1
>>> txt = "Hello, welcome to my world."
>>> 
>>> x = txt.find("e", 5, 10)
>>> 
>>> print(x)
8
>>> txt = "Hello, welcome to my world."
>>> 
>>> print(txt.find("q"))
-1
>>> print(txt.index("q"))
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ValueError: substring not found
>>> txt = "Company12"
>>> 
>>> x = txt.isalnum()
>>> 
>>> print(x)
True
>>> txt = "Company 12"
>>> 
>>> x = txt.isalnum()
>>> 
>>> print(x)
False
>>> txt = "Company10"
>>> 
>>> x = txt.isalpha()
>>> 
>>> print(x)
False
>>> a = "Hello world!"
>>> b = "hello 123"
>>> c = "mynameisPeter"
>>> 
>>> print(a.islower())
False
>>> print(b.islower())
True
>>> print(c.islower())
False
>>> txt = "Hello! Are you #1?"
>>> 
>>> x = txt.isprintable()
>>> 
>>> print(x)
True
>>> txt = "Hello!\nAre you #1?"
>>> 
>>> x = txt.isprintable()
>>> 
>>> print(x)
False
>>> 
>>> 
>>> 
>>> 
>>> 
>>> 
>>> myTuple = ("John", "Peter", "Vicky")
>>> 
>>> x = "#".join(myTuple)
>>> 
>>> print(x)
John#Peter#Vicky
>>> x = ".".join(myTuple)
>>> print(x)
John.Peter.Vicky
>>> type(x)
<class 'str'>
>>> myDict = {"name": "John", "country": "Norway"}
>>> mySeparator = "TEST"
>>> 
>>> x = mySeparator.join(myDict)
>>> 
>>> print(x)
nameTESTcountry
>>> 
>>> 
>>> device = "cs-sw-a"
>>> if device.endswith("a"):
...     print("Found device")
... else:
...     print("device not found")
... 
Found device
>>> txt = "Hello my FRIENDS"
>>> 
>>> x = txt.lower()
>>> 
>>> print(x)
hello my friends
>>> txt = "I could eat bananas all day"
>>> 
>>> x = txt.partition("bananas")
>>> 
>>> print(x)
('I could eat ', 'bananas', ' all day')
>>> x = txt.partition(" ")
>>> print(x)
('I', ' ', 'could eat bananas all day')
>>> txt = "I could eat bananas all day"
>>> 
>>> x = txt.partition("apples")
>>> 
>>> print(x)
('I could eat bananas all day', '', '')
>>> txt = "I like bananas"
>>> 
>>> x = txt.replace("bananas", "apples")
>>> 
>>> print(x)
I like apples
>>> txt = "one one was a race horse, two two was one too."
>>> 
>>> x = txt.replace("one", "three")
>>> 
>>> print(x)
three three was a race horse, two two was three too.
>>> txt = "one one was a race horse, two two was one too."
>>> 
>>> x = txt.replace("one", "three", 2)
>>> 
>>> print(x)
three three was a race horse, two two was one too.
>>> 
>>> 
>>> 
>>> txt = "Mi casa, su casa."
>>> 
>>> x = txt.rfind("casa")
>>> 
>>> print(x)
12
>>> ip = " 10.2.3.4"
>>> ip.startswith("10")
False
>>> ip.rstrip("").startswith("10")
False
>>> (ip.rstrip("")).startswith("10")
False
>>> ip.rstrip()
' 10.2.3.4'
>>> ip.rstrip().startswith("10")
False
>>> (ip.rstrip()).startswith("10")
False
>>> (ip.lstrip("")).startswith("10")
False
>>> ip.lstrip("").startswith("10")
False
>>> 
>>> ip.lstrip()
'10.2.3.4'
>>> (ip.lstrip()).startswith("10")
True
>>> ip.rstrip().startswith("10")
False
>>> ip.lstrip().startswith("10")
True
>>> 
>>> 
>>> ip.strip().startswith("10")
True
>>> txt = "I could eat bananas all day, bananas are my favorite fruit"
>>> 
>>> x = txt.rpartition("bananas")
>>> 
>>> print(x)
('I could eat bananas all day, ', 'bananas', ' are my favorite fruit')
>>> x = txt.partition("bananas")
>>> 
>>> print(x)
('I could eat ', 'bananas', ' all day, bananas are my favorite fruit')
>>> txt = "welcome to the jungle"
>>> 
>>> x = txt.split()
>>> 
>>> print(x)
['welcome', 'to', 'the', 'jungle']
>>> txt
'welcome to the jungle'
>>> print(len(x))
4
>>> type(x)
<class 'list'>
>>> txt = "hello, my name is Peter, I am 26 years old"
>>> 
>>> x = txt.split(", ")
>>> 
>>> print(x)
['hello', 'my name is Peter', 'I am 26 years old']
>>> txt = "Thank you for the music\nWelcome to the jungle"
>>> 
>>> x = txt.splitlines()
>>> 
>>> print(x)
['Thank you for the music', 'Welcome to the jungle']
>>> txt = "Thank you for the music\nWelcome to the jungle"
>>> 
>>> x = txt.splitlines(True)
>>> 
>>> print(x)
['Thank you for the music\n', 'Welcome to the jungle']
>>> 
>>> 
>>> txt = "Hello, welcome to my world."
>>> 
>>> x = txt.startswith("Hello")
>>> 
>>> print(x)
True
>>> 
>>> 
>>> ip = "10.1.1.2"
>>> ip.startswith("10.")
True
>>> txt = "Hello, welcome to my world."
>>> 
>>> x = txt.startswith("wel", 7, 20)
>>> 
>>> print(x)
True
>>> 
>>> 
>>> ip = "100.111.123.234"
>>> txt = "     banana     "
>>> 
>>> x = txt.strip()
>>> 
>>> print("of all fruits", x, "is my favorite")
of all fruits banana is my favorite
>>> txt
'     banana     '
>>> txt = ",,,,,rrttgg.....banana....rrr"
>>> 
>>> x = txt.strip(",.grt")
>>> 
>>> print(x)
banana
>>> x = txt.strip(",.tgr")
>>> print(x)
banana
>>> 
>>> 
>>> 
>>> 
>>> 
>>> if ip.lstrip().rstrip().startswith("c"):
...     if ip.lstrip().rstrip().endswith("p"):
... 
  File "<stdin>", line 3
    
IndentationError: expected an indented block after 'if' statement on line 2
>>> if ip.lstrip().rstrip().startswith("c"):
...     if ip.lstrip().rstrip().endswith("p"):
... print("this is not true")
  File "<stdin>", line 3
    print("this is not true")
IndentationError: expected an indented block after 'if' statement on line 2
>>> 
>>> 
>>> 
>>> 
>>> 
>>> ip = "10.1.1.2"
>>> ip.lstrip().rstrip().startswith() and ip.lstrip().rstrip().endswith("p")
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: startswith() takes at least 1 argument (0 given)
>>> 
>>> 
>>> ip.lstrip().rstrip().startswith("10.") and ip.lstrip().rstrip().endswith("2"):
  File "<stdin>", line 1
    ip.lstrip().rstrip().startswith("10.") and ip.lstrip().rstrip().endswith("2"):
                                                                                 ^
SyntaxError: invalid syntax
>>> 
>>> 
>>> ip = "10.1.1.2"
>>> if ip.lstrip().rstrip().startswith("10.") and ip.lstrip().rstrip().endswith("2"):
... print("Statement is true")
  File "<stdin>", line 2
    print("Statement is true")
    ^
IndentationError: expected an indented block after 'if' statement on line 1
>>> ip = "10.1.1.2"
>>> if ip.lstrip().rstrip().startswith("10.") and ip.lstrip().rstrip().endswith("2"):
...     print("Statement is true")
... 
Statement is true
>>> 
>>> 
>>> txt = ",,,,,rrttgg.....banana....rrr"
>>> 
>>> x = txt.strip(",.grt")
>>> 
>>> print(x)
banana
>>> 
>>> 
>>> 
>>> 
>>> ip = "hello 10.2.3.4"
>>> x = ip.strip(" hello")
>>> print(x)
10.2.3.4
>>> x = ip.strip(" hello").startswith("10.") and ip.strip(" hello").endswith(4):
  File "<stdin>", line 1
    x = ip.strip(" hello").startswith("10.") and ip.strip(" hello").endswith(4):
                                                                               ^
SyntaxError: invalid syntax
>>> if ip.strip(" hello").startswith("10.") and ip.strip(" hello").endswith(4):
...     print("usable IP")
... else:
...     print("absurd IP")
... 
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: endswith first arg must be str or a tuple of str, not int
>>> 
>>> 
>>> if ip.strip(" hello").startswith("10.") and ip.strip(" hello").endswith("4"):
...     print("usable IP")
... else:
...     print("absurd IP")
... 
usable IP
