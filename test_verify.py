import requests

url = "http://127.0.0.1:5000/otp"
s = requests.Session()

# 1. Request OTP
print("--- Requesting OTP ---")
data_req = {
    "action": "request",
    "email": "afnanulhaq4@gmail.com"
}
try:
    resp_req = s.post(url, data=data_req)
    print("Status:", resp_req.status_code)
    print("Body:", resp_req.json())
except Exception as e:
    print("Request failed:", e)

# 2. Verify with Wrong OTP
print("\n--- Verifying with Wrong OTP ---")
data_ver_wrong = {
    "action": "verify",
    "otp": "000000"
}
try:
    resp_ver_wrong = s.post(url, data=data_ver_wrong)
    print("Status:", resp_ver_wrong.status_code)
    print("Body:", resp_ver_wrong.json())
except Exception as e:
    print("Verify failed:", e)
