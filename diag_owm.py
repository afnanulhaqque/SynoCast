import os
import requests
from dotenv import load_dotenv

load_dotenv()
key = os.environ.get('OPENWEATHER_API_KEY')
lat, lon = 33.543576573307035, 73.08626890182497

urls = {
    "current": f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={key}",
    "forecast": f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={key}",
    "pollution": f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={key}"
}

print(f"API Key found: {'Yes' if key else 'No'}")
if key:
    print(f"Key length: {len(key)}")

for name, url in urls.items():
    try:
        res = requests.get(url, timeout=10)
        print(f"{name}: {res.status_code}")
        if not res.ok:
            print(f"  Error: {res.text}")
    except Exception as e:
        print(f"{name}: Failed with exception: {e}")
