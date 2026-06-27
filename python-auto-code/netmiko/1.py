import yaml
from jinja2 import FileSystemLoader, Environment

# Read the YAML file
with open("intf_config_data.yaml", "r") as intef_data_yaml_file:
    sw_config_data = yaml.safe_load(intef_data_yaml_file)  # Read YAML and convert into a Python list of dicts

# print("Loaded YAML Data:")
# print(sw_config_data)

# Set up the Jinja2 environment
template_loader = FileSystemLoader(searchpath=".")
env = Environment(loader=template_loader)
template = env.get_template("sw_config_template.j2")

# Render the template with the data
rendered_output = template.render(data_list=sw_config_data)  # Correct: use data_list to match Jinja2 template
config_list = rendered_output.splitlines()

# Print the rendered configuration
print("\nRendered Configuration:")
for line in config_list:
    print(line)
















import yaml  # Import YAML module
from jinja2 import FileSystemLoader, Environment  # Import Jinja2 classes

# Load YAML file safely using 'with'
with open("vlan.yaml") as yaml_file:
    sw_config_data = yaml.safe_load(yaml_file)  # Parse YAML to dict

# Set up Jinja2 environment and load the correct template file
template_loader = FileSystemLoader(searchpath=".")
env = Environment(loader=template_loader)
template = env.get_template("vlan.j2")  # Correct filename

# Render template by passing the full YAML dict as 'device_data'
rendered_output = template.render(device_data=sw_config_data)

# Print the final configuration
print(rendered_output)
