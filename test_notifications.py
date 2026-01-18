
import os
import sys
from flask import Flask
from app.utils.notifications import send_alert_email, send_otp_email

# Mock app context
app = Flask(__name__)

def test_flows():
    print("Testing Notification Flows...")
    
    # 1. Test OTP Email Construction
    print("\n[1] Testing OTP Email Construction...")
    otp = "123456"
    print(f"Generating OTP email for {otp}...")
    # We can't actually send without a key, but we can verify the function call doesn't crash
    try:
        # Check if environment provided key, otherwise expect failure/log
        res = send_otp_email("test@example.com", otp)
        print(f"Result: {res} (Expected False if no key)")
    except Exception as e:
        print(f"FAILED: {e}")

    # 2. Test Alert Email Construction
    print("\n[2] Testing Alert Email Construction...")
    alert_data = {
        "event": "Severe Thunderstorm Warning",
        "severity": "Severe",
        "description": "Damaging winds and large hail are likely. Move to an interior room on the lowest floor of a sturdy building."
    }
    advice = "Stay away from windows. Unplug electronics. Keep your emergency kit nearby."
    
    try:
        res = send_alert_email("subscriber@example.com", alert_data, advice)
        print(f"Result: {res} (Expected False if no key)")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_flows()
