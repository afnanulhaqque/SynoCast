import requests
import time

url = "http://127.0.0.1:5000/api/weather?lat=33.543576573307035&lon=73.08626890182497"

print("Testing rate limits...")
success_count = 0
error_count = 0
start_time = time.time()

# Try hitting it 35 times quickly (New limit is 30/min)
for i in range(1, 41):
    try:
        res = requests.get(url)
        if res.status_code == 200:
            success_count += 1
        elif res.status_code == 429:
            print(f"[{i}] Rate limit hit (429): {res.json()}")
            error_count += 1
        else:
            print(f"[{i}] Unexpected status {res.status_code}: {res.text}")
            error_count += 1
    except Exception as e:
        print(f"[{i}] Request failed: {e}")
        error_count += 1
    
    if i % 10 == 0:
        print(f"Progress: {i}/40 requests...")

duration = time.time() - start_time
print(f"\nSummary:")
print(f"Successes: {success_count}")
print(f"Errors (should include some 429s after 30): {error_count}")
print(f"Duration: {duration:.2f}s")
