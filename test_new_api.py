import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_trip_plan():
    print("Testing AI Trip Planner...")
    data = {"destination": "Paris", "dates": "May 1-10", "purpose": "leisure"}
    try:
        res = requests.get(f"{BASE_URL}/api/trip_plan", params=data)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text}")
    except Exception as e:
        print(f"Error: {e}")

def test_historical():
    print("\nTesting Historical Insights...")
    params = {"lat": 48.8566, "lon": 2.3522, "years": 5}
    try:
        res = requests.get(f"{BASE_URL}/api/weather/historical", params=params)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_trip_plan()
    test_historical()
