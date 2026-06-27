import json
import csv

# Sample JSON data
json_data = {
  "Name": "Aadarsh",
  "Age": 28,
  "Location": "Delhi"
}

# Write to CSV where keys are rows
with open ('output.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Key", "Value"])
    for k, v in json_data.items():
        writer.writerow([k, v])

print("CSV file created successfully")
