class calc:
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


obj1 = calc()
output = obj1.add(10, 20)
print(output)

output = obj1.subtract(30, 10)
print(output)

output = obj1.multiply(30, 10)
print(output)

