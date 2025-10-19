import requests

url = "http://127.0.0.1:3500/token"
params = {"name": "Alice"}

response = requests.post(url, params=params)
print(response.json())
