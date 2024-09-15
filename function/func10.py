# variable argument 

def add(*var):  #varibale argument
    print(var)

x = 10
y = 20
z = 30
p = 1
q = 2
r = 3

add(x, y, z, p, q, r)    

# positional & variable Argument

def add (a, b, c, *var):
    print(a)
    print(b)
    print(c)
    print(var)
    
x = 10
y = 20
z = 30
p = 1
q = 2
r = 3

add(x, y, z, p, q, 10)    

""" 
def add (*var, a, b, c):
    print(a)
    print(b)
    print(c)
    print(var)
    
x = 10
y = 20
z = 30
p = 1
q = 2
r = 3

add(x, y, z, p, q, 10)    

error ====> add() missing 3 required keyword-only arguments: 'a', 'b', and 'c'
    
   """  


