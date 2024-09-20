import yaml
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler


# Load YAML data
with open('bgp-interface-data-cred.yaml', "r") as file:
    router_data = yaml.safe_load(file)
# print(router_data)    

# Set up Jinja2 environment and template
env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('bgp-template.j2')

# Render the configuration from the template and YAML data
config = template.render(routers=router_data['routers'])
# print(config)

# Output the generated configuration
# print(config)

# Optionally, you can save the configuration to a file
with open('router_configurations.txt', 'w') as config_file:
    config_file.write(config)

# Iterate over each router in YAML data
for router in router_data['routers']:
    # Render configuration for each router
    config = template.render(routers=[router])
    
    # Display the configuration that will be pushed
    print(f"\nPushing the following configuration to {router['name']}:\n")
    print(config)
    
    # Netmiko device configuration
    device = {
    'device_type': 'cisco_ios',
    'host': router['host'],
    'username': router['username'],
    'password': router['password'],
    'secret': router['secret'],
    }

    # try:
    # Establish SSH connection
    connection = ConnectHandler(**device)

    # Enter enable mode
    connection.enable()

    # Push configuration
    output = connection.send_config_set(config.splitlines())



    # Print the output from the device
    print(output)
        
    # Disconnect from the device
    connection.disconnect()
# except Exception as e:
# print(f"Failed to push configuration to {router['name']}: {e}")

print("Configuration push complete.")




""" 
import yaml
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler

# Load YAML data
with open('routers.yaml') as file:
    router_data = yaml.safe_load(file)

# Set up Jinja2 environment and template
env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('template.j2')

# Iterate over each router in YAML data
for router in router_data['routers']:
    # Render configuration for each router
    config = template.render(routers=[router])
    
    # Display the configuration that will be pushed
    print(f"\nPushing the following configuration to {router['name']}:\n")
    print(config)
    
    # Netmiko device configuration
    device = {
        'device_type': 'cisco_ios',
        'host': router['host'],
        'username': router['username'],
        'password': router['password'],
        'secret': router['secret'],
    }

    try:
        # Establish SSH connection
        connection = ConnectHandler(**device)
        
        # Enter enable mode
        connection.enable()
        
        # Push configuration
        output = connection.send_config_set(config.splitlines())
        
        # Save configuration
        connection.save_config()
        
        # Print the output from the device
        print(output)
        
        # Disconnect from the device
        connection.disconnect()
    except Exception as e:
        print(f"Failed to push configuration to {router['name']}: {e}")

print("Configuration push complete.")






 """