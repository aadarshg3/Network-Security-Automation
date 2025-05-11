class Calc:
    
    def __init__(self, a, b):
        self.a = a
        self.b = b
    
    def add(self):
        return self.a + self.b
    
    
    def sub(self):
        return self.a - self.b
    
    def mul(self):
        return self.a * self.b
    
    @staticmethod

    def div(a, b):
        return a/b
    
x = 5 
y = 10   
obj1 = Calc(x, y)

print(obj1.add())
print(obj1.sub())
print(obj1.mul())
print(obj1.div(10, 5))


