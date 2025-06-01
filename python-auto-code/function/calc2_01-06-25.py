def add(a , b):
    return a + b
def subtract(a , b):
    return a - b
def multiply(a , b):
    return a * b
def divide(a , b):
    if b == 0:
        return "Error: cannot divide by zero"
    return a / b


a = 10
b = 2

print("sum is:", add(a, b))
print("subtraction is:", subtract(a, b))
print("multiplication is:", multiply(a, b))
print("division is:", divide(a, b))
