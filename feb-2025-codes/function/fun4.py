def network_ping():
    return "Pinged device!"

def wrapper(func):
    print("Trying to connect...")
    result = func()
    print("Connection successful")
    return result

output = wrapper(network_ping)
print("Output:", output)