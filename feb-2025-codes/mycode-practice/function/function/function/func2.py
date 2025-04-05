





"""

# Que:1)  Create a function configure_device(device_name, *interfaces)
# that prints all interfaces to be configured.
def configure_device(device_name, *interfaces):
    if not interfaces:
        print("No interfaces provided for {device_name}")
    else:
        for intf in interfaces:
            print(f"configuring {intf} of {device_name}:")


Ex: configure_device("Switch1", "Gig0/1", "Gig0/2", "Gig0/3")
===output===
configuring Gig0/1 of Switch1:
configuring Gig0/2 of Switch1:
configuring Gig0/3 of Switch1:


# Que:2) Create a function set_hostname(device, **settings)
# that prints hostname, location, and domain (if given).

def set_hostname(device, **settings):
    print(f"setting hostname of {device} with parameters:")
    for key, value in settings.items():
        print(f"{key}: {value}")

# Example of below:
set_hostname("router1", hostname="R1-core", location="DC1", domain="example.com")
===output===
[mycode-practice]$ python3 func2.py 
setting hostname of router1 with parameters:
hostname: R1-core
location: DC1
domain: example.com
[mycode-practice]$ 

# ✍️ Task:
# Create a function called setup_device() that:

# Takes one positional argument: device

# Takes multiple interfaces using *interfaces

# Takes optional configuration parameters using **config

# Then it should:

# Print the device name

# Print each interface it will configure

# Print all config parameters like hostname, domain, SNMP, etc.

def setup_device(device, *interfaces, **config):
    print(f"\nSetting up device: {device}\n")

    if interfaces:
        print("configuring interfaces:")
        for intf in interfaces:
            print(f"- {intf}")
    else:
        print("No interface provided.")
    if config:
        print("\nApplying configuration:")
        for k, v in config.items():
            print(f"{k}: {v}")
    else:
        print("\nNo additional configuration provides")


setup_device(
    "Router1",
    "Gig0/1", "Gig0/2", 
    hostname="R1-Core",
    domain="example.com"

)

=====output=======
[mycode-practice]$ python3 func2.py 

Setting up device: Router1

configuring interfaces:
- Gig0/1
- Gig0/2

Applying configuration:
hostname: R1-Core
domain: example.com



"""