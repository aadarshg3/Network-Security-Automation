#!/usr/bin/env python3

""" def cal (a, b, c):
    add = (a + b + c)
    sub = (c - b - a)
    mul = (a * b * c)
    div = (a / b )
    return add , sub, mul, div

temp1 = cal (10, 20, 30)
print(temp1)

for value in temp1:
    print(value) """

# above is not the good practice to write function.

def add(a, b, c):
    sum = (a + b + c)
    return sum

def sub(a, b):
    sub1 = (b - a) 
    sub2 = (a - b)
    return sub1, sub2


def mul(a, b, c):
    mul1 = (a * b * c) 
    return mul1


# calling it

output1 = add (10, 20, 40)
output2 = sub (90, 40)
output3 = mul(4, 6, 2)

print(output1)
print(output2)
print(output3)










""" 
def multi(a, b):
    xyz = a * b
    return xyz

temp = multi(10 , 20)
print(temp) 

def sub(a, b):
    xyz = a - b
    return xyz

temp = multi(10 , 20)
print(temp) 


"""