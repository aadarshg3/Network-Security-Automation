import yaml
from jinja2 import FileSystemLoader, Environment


with open("test.yaml", "r") as yaml_file:
    bgpconfig = yaml.safe_load(yaml_file)
print(bgpconfig)

# env = Environment(FileSystemLoader(searchpath=(".")))
# =====>>>> line 9 & 10 are same as 12

template_loader = FileSystemLoader(searchpath=".")
env = Environment(loader=template_loader)

template = env.get_template("test.j2")
# print(template)

rendered_output = template.render(bgp=bgpconfig)
print(rendered_output)
 
