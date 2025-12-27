## 🚀 Quick Fix Commands

### 1. Generate VAPID Keys

```powershell
cd d:\SynoCast
.\.venv\Scripts\python.exe gen_keys_v2.py
```

### 2. Save Keys to File (for easy copy/paste)

```powershell
.\.venv\Scripts\python.exe gen_keys_v2.py | Out-File -FilePath vapid_keys_output.txt -Encoding UTF8
notepad vapid_keys_output.txt
```

### 3. After Adding to Vercel, Verify Locally

```powershell
# Check what env vars you have locally
Get-Content .env | Where-Object { $_ -match '^[A-Z_]+=.+' } | ForEach-Object { ($_ -split '=')[0] }
```

---

## 📋 Vercel Setup Checklist

Go to: https://vercel.com/dashboard → syno-cast → Settings → Environment Variables

Add these 7 variables (select ALL environments for each):

- [ ] FLASK_SECRET_KEY (copy from .env)
- [ ] OPENWEATHER_API_KEY (copy from .env)
- [ ] RESEND_API_KEY (copy from .env)
- [ ] GEMINI_API_KEY (copy from .env)
- [ ] NEWS_API_KEY (copy from .env)
- [ ] VAPID_PRIVATE_KEY (from gen_keys_v2.py output)
- [ ] VAPID_PUBLIC_KEY (from gen_keys_v2.py output)

Then: Deployments → Latest → ⋯ → Redeploy

---

## ✅ Test Commands

```powershell
# Test health endpoint
Invoke-WebRequest -Uri "https://syno-cast.vercel.app/health" -UseBasicParsing

# Test main page
Invoke-WebRequest -Uri "https://syno-cast.vercel.app/" -UseBasicParsing
```

If successful, you'll see HTTP 200 instead of 500!
