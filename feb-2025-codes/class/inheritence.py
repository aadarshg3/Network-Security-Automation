class calc:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def add (self):
        return self.a + self.b
    
    def sub(self):
        return self.a - self.b
    
class mycalc(calc):
    # def mul(self, a, b):
    #     return a * b
    
    def mul(self, c):
        return self.a * self.b * c
    def add (self, d):
        return self.a + self.b + d


myobj1 = mycalc(11, 11)
var1 = myobj1.mul(2)
print(var1)
var2 = myobj1.add(3)
print(var2)


var3 = super().add()
print(var3)