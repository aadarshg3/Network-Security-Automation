import yaml

with open("yaml-data.yaml", "r") as yaml_file:
    bgpconfig = yaml.safe_load(yaml_file)
# print(bgpconfig)    


for k,v in bgpconfig.items():
    print(v)
    for item in v:
        # print(item)
        for k1,v1 in item.items():
            print(v1)

                
                
with open("yaml-data.yaml", "w") as yaml_file1:
    updated_data = yaml.dump(bgpconfig,yaml_file1,indent=4)
print(updated_data)                    