import json


# with open("j1.json", "r") as f:
#     data = json.load(f)

json_data = {"router": "R1", "uptime": "5 days"}
json_str = json.dumps(json_data)
output = json.loads(json_data)
print(output)