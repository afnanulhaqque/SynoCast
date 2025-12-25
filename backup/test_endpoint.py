import requests

url = "http://127.0.0.1:5000/api/ai_chat"
payload = {
    "message": "Hello",
    "lat": 33.6844,
    "lon": 73.0479
}

try:
    # We might need to handle CSRF if we call it this way, 
    # but let's see if it fails with 400 or something else.
    # Actually, SeaSurf might block it.
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
