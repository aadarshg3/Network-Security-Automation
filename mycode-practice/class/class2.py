class Switch:
    def __init__(self, name, interface):
        self.name = name
        self.interface = interface

    def show_config(self):
        print(f"switch name is: {self.name}")
        print(f"interface is: {self.interface}")

    def __str__(self):
        return f"Switch(Name: {self.name}, Interface: {self.interface})"
    
    def __repr__(self):
        return f"Switch('{self.name}', '{self.interface}')"
    

s1 = Switch("Core-Sw1", "Gig0/1")
print(s1)
# obj1 = Switch("Core-Sw1", "Gig0/1")
# obj1.show_config()
