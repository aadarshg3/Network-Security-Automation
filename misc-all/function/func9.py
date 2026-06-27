# Positional Argument Lab

def add(a, b, c):
    print(a)
    print(b)
    print(c)


x = 10
y = 20
z = 30

# add (x , y )   #===> Error add() missing 1 required positional argument
add (x, y, z)

# ===========================================================================
def add(a, b):
    print(a)
    print(b)
    # print(c)


a = 10
b = 20
c = 30

add (a , b, c)  # ====> add() takes 2 positional arguments but 3 were given

# =============================================================================
