class calc:

    def __init__(self, a, b):
        print("I am in init method")
        self.a = a
        self.b = b

    def add(self):

        sum = self.a + self.b
        return sum
    
    def sub(self):
        return self.a - self.b
        
obj1 = calc(20, 30)
sum = obj1.add()
print(sum)

# sub = obj1.sub()
# print(sub)


# obj2 = calc(200, 300)
# sum = obj2.add()
# print(sum)

# sum = obj1.add()
# print(sum)