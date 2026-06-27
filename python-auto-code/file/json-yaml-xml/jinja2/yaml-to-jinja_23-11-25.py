import yaml
from jinja2 import Environment, FileSystemLoader

# path where tempates are stored

env = Environment(loader=FileSystemLoader("."))

# load template file
template = env.get_template("templates/sw-config.j2")


