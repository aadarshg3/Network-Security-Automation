import json

with open ("config_data.json", "r") as file: 
    py_data = json.load(file)  
print(file)     
print(py_data)     
print(type(py_data))



