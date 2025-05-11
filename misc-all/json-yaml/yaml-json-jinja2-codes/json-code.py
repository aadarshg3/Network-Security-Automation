import json

with open("json-data.json", "r") as json_data:
    bgp_conf_data = json.load(json_data) 

# json.load converts json into python dictionary.    
# json.dump converts 
     
# print(bgp_conf_data)    

for k, v in bgp_conf_data.items():
    # print(k)
    for item in v:
        # print(item)
        for k1,v1 in item.items():
            print('\t', k1)
            for k2,v2 in v1.items():
                print('\t', '\t', k2,v2)
    
# bgp_conf_data["local-AS"] = 400   # editing value of local-AS


with open("json-data1.json", "w") as json_dict: # opening a file
    json_read_data = json.dump(bgp_conf_data, json_dict, indent=4) # writing back to json file

# to write to the file we have dump method, as we changed local-AS-400 
# and written to the file
# print(json_read_data)
    
    