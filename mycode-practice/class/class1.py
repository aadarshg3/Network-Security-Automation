class Router:
    def __init__(self, hostname, location):
        self.hostname = hostname
        self.location = location
    
    def show_info(self):
        print(f"Router Name: {self.hostname}")
        print(f"Location: {self.location}")

    def updated_location(self, new_location):
        self.location = new_location
        print(f"Location updated to: {self.location}")

r1 = Router("Core-R1", "Delhi")
r1.updated_location("mumbai")
r1.show_info()


