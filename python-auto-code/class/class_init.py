class Calc:

    #  def __init__(self) -> None : #whenever we create an object, this  . Self Binding ke liye hota hai
    #      pass
        
    #  def __init__(self):  # above and this code block is same
    #      return None
    
    def __init__(self, a, b):  # above and this code block is same
         self.a = a
         self.b = b
                  
         
    def add(self):
        return self.a + self.b 
      
        
    def sub(self):
        return self.a - self.b     

    def mul(self):
        return self.a * self.b 

# obj1 = Calc() # creating object of class Calc, copy of Calc

obj1 = Calc() # creating object of class Calc, copy of Calc