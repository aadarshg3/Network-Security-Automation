import time
import requests

for i in range(5):  # Retry 5 times
    try:
        response = requests.get("https://api.example.com", timeout=5)
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 2))
            time.sleep(retry_after)
        else:
            break
    except requests.exceptions.RequestException:
        time.sleep(2 ** i)  # Exponential backoff

# ====================
import requests

response = requests.get("https://jsonplaceholder.typicode.com/posts/1")
print(response.status_code)
print(response.json())


data = {"title": "foo", "body": "bar", "userId": 1}
response = requests.post("https://jsonplaceholder.typicode.com/posts", json=data)
print(response.status_code)
print(response.json())


data = {"id": 1, "title": "new", "body": "content", "userId": 1}
response = requests.put("https://jsonplaceholder.typicode.com/posts/1", json=data)
print(response.status_code)


update = {"title": "updated title"}
response = requests.patch("https://jsonplaceholder.typicode.com/posts/1", json=update)
print(response.json())

response = requests.delete("https://jsonplaceholder.typicode.com/posts/1")
print(response.status_code)  # Should return 200 or 204
