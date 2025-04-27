import yaml
from jinja2 import FileSystemLoader, Environment

# Read the YAML file
with open("intf_config_data.yaml", "r") as intef_data_yaml_file:
    sw_config_data = yaml.safe_load(intef_data_yaml_file)  # Read YAML and convert into a Python list of dicts

print("Loaded YAML Data:")
print(sw_config_data)

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
