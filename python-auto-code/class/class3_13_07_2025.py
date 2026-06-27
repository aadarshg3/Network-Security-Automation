class calc:

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def add(self):
        return self.a + self.b
    def subtract(self):
        return self.a - self.b
    def multiply(self):
        return self.a * self.b


class newcalc(calc):
    def div(self):
        return self.a / self.b
    
obj1_a = newcalc(100, 200)
output1 = obj1_a.add()
print(output1)

output2 = obj1_a.div()
print(output2)