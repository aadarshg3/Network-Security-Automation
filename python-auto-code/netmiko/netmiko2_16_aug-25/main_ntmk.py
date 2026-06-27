import yaml
from pprint import pprint
from netmiko import ConnectHandler
from jinja2 import Environment, FileSystemLoader

with open("inv/switch.yaml", "r") as file:
  devices = yaml.safe_load(file)

for device in devices:
    # Path where templates are stored
    env = Environment(loader=FileSystemLoader("."))

    # Load template file
    template = env.get_template("templates/sw-config.j2")

    with open("data/config-data.yaml", "r") as file:
      config = yaml.safe_load(file)

    # pprint(config)
    # Render template
    output = template.render(config_info=config)
    # print(output)
    config_commands = output.splitlines()
    # print(config_commands)

    net_connect = ConnectHandler(**device)
    output = net_connect.send_config_set(config_commands)
    print(output)