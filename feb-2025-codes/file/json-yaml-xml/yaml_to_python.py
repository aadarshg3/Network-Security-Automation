import yaml

with open ("intf_config_data.yaml", "r") as file: 
    py_data = yaml.safe_load(file)
  
print(py_data)     




