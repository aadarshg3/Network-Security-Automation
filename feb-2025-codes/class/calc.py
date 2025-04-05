class Calc:
    # def __init__():   #whenever we create an object, this 
    def __init__(self, a , b):   #whenever we create an object, this  . Self Binding ke liye hota hai
        self.a = a
        self.b = b
        
    def add(self):
        # output = (a + b)
        return self.a + self.b 
        # return output
        
    def sub(self):
        return self.a - self.b     
    
    @staticmethod #Python Decorator to tell the interpreter that it is static method
    def mul(a, b):
        return a * b 
    

# obj1 = Calc() # creating object of class Calc, copy of Calc



# x = 100
# y = 50
# obj1 = Calc(x, y) # creating object of class Calc, copy of Calc

# print(obj1.add())
# print(obj1.sub())
# print(obj1.mul(10, 5))

# class Newcalc:
class Newcalc(Calc): #Calc ki sari property inherit ho jati hai newcalc me
    

    # def __init__(self, a, b):
    #     self.a = a
    #     self.b = b

    def div(self):
        div = self.a/self.b
        return div

new_class_obj1 = Newcalc(22, 33)
tempvar = new_class_obj1.add()
print(tempvar)

tempvar = new_class_obj1.div()
print(tempvar)


# var1 = copy1_of_calc.add(10, 20)
# print(var1)
# test2 = copy1_of_calc.sub(20, 10)
# test3 = copy1_of_calc.mul(2, 4)

# print(test2)
# print(test3)





