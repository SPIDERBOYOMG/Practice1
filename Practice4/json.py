import json

with open("sample-data.json") as f:
    data = json.load(f)

interfaces = data["imdata"]

for item in interfaces:
    attributes = item["l1PhysIf"]["attributes"]
    print(f"Interface: {attributes['id']}, Switching State: {attributes['switchingSt']}")
