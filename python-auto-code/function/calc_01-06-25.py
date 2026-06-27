
a = 10 
b = 20
def addition(a, b):
    #operation
    a = a + 30
    print("value of a inside of the function", a)
    s = a + b
    return s

a = 10
b = 20 


# return
# print(s)
# calling function
# output = addition(c, d)
output = addition(a, b)
print(output)
print("value of a outside of the function", a)
