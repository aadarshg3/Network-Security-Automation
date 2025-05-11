from napalm import get_network_driver

# Define device credentials and details
device_details = {
    "hostname": "192.168.1.212",  # Replace with the actual router IP
    "username": "netg",        # Replace with your router's username
    "password": "netg",     # Replace with your router's password
    "optional_args": {},        # Any optional arguments (e.g., port, secret for enable mode)
}

# Initialize the driver for Cisco IOS
driver = get_network_driver("ios")

# Connect to the device
device = driver(
    hostname=device_details["hostname"],
    username=device_details["username"],
    password=device_details["password"],
    optional_args=device_details["optional_args"]
)

# Open the connection
print("Connecting to device...")
device.open()

# Get interface information
interfaces = device.get_interfaces()
print(interfaces)
print(type(interfaces))


# Print the interface details
# print("Interface Information:")
# for interface, details in interfaces.items():
#     print(f"Interface: {interface}")
#     for key, value in details.items():
#         print(f"  {key}: {value}")

# Close the connection
device.close()
print("Connection closed.")
print("Connection closed.")
