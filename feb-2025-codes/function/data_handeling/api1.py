import requests

try:
    response = requests.get("https://api.example.com/data", timeout=5)
    response.raise_for_status()
except requests.exceptions.Timeout:
    print("Request timed out. Retrying...")
except requests.exceptions.HTTPError as err:
    print(f"HTTP error occurred: {err}")
