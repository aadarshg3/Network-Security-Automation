import yaml

yaml_read_file = open("hw7.yaml", "r")
yaml_read_data = yaml.safe_load(yaml_read_file)
print(yaml_read_data)


