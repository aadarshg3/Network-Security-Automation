def add (a, b, c, *var, ssl=False, verbose =0, **kvar):

    print(a)
    print(b)
    print(c)
    print(var)
    print(ssl)
    print(verbose)
    print(kvar)
    
x = 10.2
y = 20
z = 30
p = 1
q = 2
r = 3
data = {'abc': 'test1', 'xyz': 'test2', 'lmn': 'test3'}

# add(x, y, z, p, q, x, ssl=True)
# add(x, y, z, p, q, x)
# add(x, y, z, p, q, x, ssl=True,verbose=1, abc="test1", xyz="test2", lmn="test3")
add(x, y, z, p, q, x, ssl=True,verbose=1, **data)

# Note: line 21 and 22 are same 

# Note: when you pass values in variable keyword argument the data is stored in Tuple.
# And when you pass your data in variable keyword argument it saves the data in dictionary.