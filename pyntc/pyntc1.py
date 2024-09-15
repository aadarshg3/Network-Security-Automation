from pyntc import ntc_device as NTC
import os

# Define the device details
device_details = {
    "host": "192.168.1.212",      # Replace with your device IP address
    "username": "netg",         # Replace with your device username
    "password": "netg",      # Replace with your device password
    "device_type": "cisco_ios_ssh",  # Device type for Cisco IOS
}

# Define backup directory and file name
backup_dir = "./backups"
backup_file = f"{backup_dir}/{device_details['host']}_backup.txt"

# Ensure backup directory exists
if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)

# Connect to the device using Pyntc
device = NTC(host=device_details["host"],
             username=device_details["username"],
             password=device_details["password"],
             device_type=device_details["device_type"])

# Open connection
device.open()
print(f"Connected to {device_details['host']}")

# Get the running configuration using the show command
running_config = device.show("show running-config")

# Save the running configuration to a file
with open(backup_file, "w") as file:
    file.write(running_config)

print(f"Backup completed. Configuration saved to: {backup_file}")

# Close the connection
device.close()
print(f"Disconnected from {device_details['host']}")
