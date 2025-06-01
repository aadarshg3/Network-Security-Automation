def calc_func(sub, *args):
    # print(type(args))
    print(args)
    s = 0
    for item in args:
        # s = s + item 
        s += item
    m = 1
    for item in args:
        m *= item
    # sub = 400
    for item in args:
        sub -= item     

    return [s , m , sub]


a = 10
b = 20
c = 30
d = 40

# calling function
# sum, mul, sub = calc_func(a, b, c, d, 10, 20, 3, 4)
# print(sum, mul, sub)
output = calc_func(300, a, b, c, d, 10, 20, 3, 4)
print(output)
print(type(output))
