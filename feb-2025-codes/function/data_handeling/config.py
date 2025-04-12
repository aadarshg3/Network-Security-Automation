import json
import csv
import os

def load_json(file_path):
    """Loads JSON data from a file."""
    with open(file_path, 'r') as file:
        return json.load(file)

def convert_json_to_csv(json_data, output_file):
    """Converts a flat JSON dictionary to a two-column CSV file."""
    with open(output_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Key", "Value"])  # header row
        for key, value in json_data.items():
            writer.writerow([key, value])

if __name__ == "__main__":
    input_file = 'input.json'
    output_file = 'output.csv'

    if os.path.exists(input_file):
        data = load_json(input_file)
        convert_json_to_csv(data, output_file)
        print(f"CSV successfully created: {output_file}")
    else:
        print(f"Input file does not exist: {input_file}")
