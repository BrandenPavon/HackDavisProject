import requests

url = "http://127.0.0.1:5000/flex-data"

payload = {
    "session_id": "session_001",
    "data": [512, 518, 521, 519, 530, 528]
}

response = requests.post(url, json=payload)

print(response.status_code)
print(response.json())
