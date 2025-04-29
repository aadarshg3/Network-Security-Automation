import yaml
from jinja2 import FileSystemLoader, Environment

with open("intf_config_data.yaml", "r") as intef_data_yaml_file:
    sw_config_data = yaml.safe_load(intef_data_yaml_file)

template_loader = FileSystemLoader(searchpath=".")
env = Environment(loader=template_loader)
template = env.get_template("sw_config_template.j2")

rendered_output = template.render(data_list=sw_config_data)

print(rendered_output)
