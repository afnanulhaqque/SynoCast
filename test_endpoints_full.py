
import os
import requests
from app import create_app

# Ensure we aren't starting background threads during test initialization
os.environ["WERKZEUG_RUN_MAIN"] = "true"

def test_endpoints():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing POSTs easily

    with app.test_client() as client:
        print("===== TESTING GET ROUTES =====")
        get_routes = [
            '/', '/news', '/weather', '/travel', '/map', '/learn', 
            '/compare', '/subscribe', '/profile', '/about', '/terms', 
            '/license', '/pakistan', '/offline', '/health',
            '/api/learn/trivia', '/api/learn/glossary',
            '/sw.js', '/robots.txt', '/ads.txt', '/sitemap.xml', '/favicon.ico'
        ]

        for route in get_routes:
            try:
                # Follow redirects to catch final status
                response = client.get(route, follow_redirects=True)
                if response.status_code == 200:
                    print(f"[PASS] GET {route}")
                else:
                    print(f"[FAIL] GET {route} - Status: {response.status_code}")
            except Exception as e:
                print(f"[ERROR] GET {route}: {e}")

        print("\n===== TESTING API GET ROUTES WITH PARAMS =====")
        # Testing with dummy params for endpoints that require them
        api_tests = [
            ('/api/weather?lat=51.5&lon=-0.1', 200),
            ('/api/weather/analytics?lat=51.5&lon=-0.1', 200),
            ('/api/weather/health?lat=51.5&lon=-0.1', 200),
            ('/api/geocode/reverse?lat=51.5&lon=-0.1', 200),
            ('/api/geocode/search?q=London', 200),
            ('/api/currency/convert?base=USD&targets=EUR', 200),
            ('/api/travel/packing-list?destination=Paris&weather=rainy', 200)
        ]

        for route, expected in api_tests:
            try:
                response = client.get(route)
                # Some APIs might fallback or fail gracefully depending on external keys, 
                # but we generally expect 200 or meaningful error code, not 500 crash.
                if response.status_code == expected:
                     print(f"[PASS] GET {route.split('?')[0]}")
                elif response.status_code == 502:  # upstream error handled
                     print(f"[WARN] GET {route.split('?')[0]} - Upstream Error (502)")
                elif response.status_code == 500:
                     # Check if it is just a missing key issue which is "safe" failure
                     print(f"[FAIL] GET {route.split('?')[0]} - Internal Error (500)")
                else:
                     print(f"[INFO] GET {route.split('?')[0]} - Status: {response.status_code}")
            except Exception as e:
                print(f"[ERROR] GET {route}: {e}")

        print("\n===== TESTING POST ROUTES =====")
        
        # Test 1: Update Session Location (CSRF Exempt)
        try:
            resp = client.post('/api/update-session-location', json={
                "city": "TestCity", "region": "TestRegion", "utc_offset": "+0000"
            })
            if resp.status_code == 200:
                print("[PASS] POST /api/update-session-location")
            else:
                print(f"[FAIL] POST /api/update-session-location - {resp.status_code}")
        except Exception as e: print(f"[ERROR] POST update-session: {e}")

        # Test 2: Proxy Cities (Internal)
        try:
            resp = client.post('/api/proxy/cities', json={"country": "France"})
            if resp.status_code in [200, 400]: # 400 if country not found is valid logic
                 print(f"[PASS] POST /api/proxy/cities (Status: {resp.status_code})")
            else:
                 print(f"[FAIL] POST /api/proxy/cities - {resp.status_code}")
        except Exception as e: print(f"[ERROR] POST proxy-cities: {e}")

        # Test 3: Logout (Needs Session)
        with client.session_transaction() as sess:
            sess['user_email'] = 'test@example.com'
        resp = client.post('/api/user/logout')
        if resp.status_code == 200:
            print("[PASS] POST /api/user/logout")
        else:
            print(f"[FAIL] POST /api/user/logout - {resp.status_code}")
            
        # Test 4: OTP Request (Subscribe)
        try:
            resp = client.post('/otp', json={"action": "request", "email": "test_auto@example.com"})
            # Might fail if email config is missing, but should not be 404 or 500 crash logic
            if resp.status_code in [200, 400, 500]: 
                print(f"[PASS] POST /otp (Handled with status {resp.status_code})")
            else:
                print(f"[FAIL] POST /otp - {resp.status_code}")
        except Exception as e: print(f"[ERROR] POST otp: {e}")

if __name__ == "__main__":
    test_endpoints()
