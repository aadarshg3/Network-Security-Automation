# get_config.py

import requests
from device_info import device, HEADERS
from requests.auth import HTTPBasicAuth

url = f"https://{device['host']}:{device['port']}/restconf/data/Cisco-IOS-XE-native:native"

response = requests.get(
    url,
    auth=HTTPBasicAuth(device["username"], device["password"]),
    headers=HEADERS,
    verify=False  # Disable SSL warnings for self-signed certs
)

print(response.status_code)
print(response.json())
