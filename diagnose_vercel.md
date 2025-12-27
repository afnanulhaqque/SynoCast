# 🔍 Diagnose Vercel 500 Error - Step by Step

## ⚡ Quick Diagnosis (Do This First!)

### Option 1: Check Health Endpoint (Fastest)

Open this URL in your browser:

```
https://syno-cast.vercel.app/health
```

**What you'll see:**

✅ **If app is working:**

```json
{
  "status": "ok",
  "environment": "vercel",
  "env_vars_set": {
    "FLASK_SECRET_KEY": true,
    "OPENWEATHER_API_KEY": true,
    ...
  }
}
```

❌ **If app is broken:**
You'll see a detailed error page showing exactly what's wrong.

---

### Option 2: Use PowerShell to Get Error Details

Run this command in PowerShell:

```powershell
# Get the health check response
Invoke-WebRequest -Uri "https://syno-cast.vercel.app/health" -UseBasicParsing | Select-Object -ExpandProperty Content
```

Or to see the main page error:

```powershell
# Get the main page response (will show error details)
Invoke-WebRequest -Uri "https://syno-cast.vercel.app/" -UseBasicParsing | Select-Object -ExpandProperty Content
```

---

## 📊 Check Vercel Dashboard Logs

### Step-by-Step:

1. **Go to Vercel Dashboard:**

   - Open: https://vercel.com/dashboard
   - Click on your **"syno-cast"** project

2. **View Latest Deployment:**

   - Click **"Deployments"** tab at the top
   - Click on the **most recent deployment** (top of the list)

3. **Check Function Logs:**

   - Scroll down to **"Functions"** section
   - Click on **"/api/index"** function
   - Look for **RED error messages**
   - **Copy the entire error message**

4. **Check Runtime Logs:**
   - Click on **"Runtime Logs"** tab
   - Look for any errors when the page loads
   - **Copy any error messages you see**

---

## 🔧 Most Common Fixes

### Fix 1: Missing Environment Variables (90% of cases)

**Check if these are set in Vercel:**

1. Go to: https://vercel.com/dashboard
2. Click **"syno-cast"** → **"Settings"** → **"Environment Variables"**
3. Verify ALL of these exist:

- [ ] `FLASK_SECRET_KEY`
- [ ] `OPENWEATHER_API_KEY`
- [ ] `RESEND_API_KEY`
- [ ] `GEMINI_API_KEY`
- [ ] `NEWS_API_KEY`
- [ ] `VAPID_PRIVATE_KEY`
- [ ] `VAPID_PUBLIC_KEY`

**If any are missing:**

1. Click **"Add New"** button
2. Enter the variable name
3. Copy the value from your local `.env` file
4. Select **"Production"**, **"Preview"**, and **"Development"**
5. Click **"Save"**
6. **IMPORTANT:** After adding all variables, click **"Deployments"** → **"Redeploy"** on the latest deployment

---

### Fix 2: Check for Import Errors

**If logs show something like:**

```
ModuleNotFoundError: No module named 'xyz'
```

**Fix:**

1. Add the missing module to `requirements.txt`
2. Commit and push:
   ```bash
   git add requirements.txt
   git commit -m "Add missing dependency"
   git push
   ```

---

### Fix 3: Database Issues

**If logs show:**

```
sqlite3.OperationalError: unable to open database file
```

**This is expected on first run.** The app should auto-create the database. If it keeps failing:

1. Check if `subscriptions.db` is in `.gitignore` (it should be)
2. The app will create it automatically on Vercel

---

## 🎯 What to Send Me

After checking the above, please share:

1. **The output from the health endpoint** (copy/paste the JSON or error message)
2. **The error from Vercel Function Logs** (if you can access them)
3. **List of environment variables you have set** (just the names, not the values)

Example:

```
Health endpoint shows:
{
  "status": "error",
  "error": {
    "type": "KeyError",
    "error": "'FLASK_SECRET_KEY'",
    ...
  }
}

Environment variables I have set:
- OPENWEATHER_API_KEY
- GEMINI_API_KEY
(missing FLASK_SECRET_KEY)
```

---

## 🚫 What to Ignore

These are **NOT** the problem:

- ❌ Zustand deprecation warnings (from Vercel's monitoring code)
- ❌ `instrument.js` warnings (Vercel's internal code)
- ❌ Favicon 500 error (will fix itself when main error is fixed)

**Only focus on:**

- ✅ The actual 500 error from your Python backend
- ✅ Missing environment variables
- ✅ Import/module errors in the logs

---

## 🔄 After Making Changes

**Always remember:**

1. After adding environment variables → **Redeploy**
2. After changing code → **Commit and push** (Vercel auto-deploys)
3. Wait 1-2 minutes for deployment to complete
4. Test again

---

## 📞 Need Help?

Run the health check command and share the output:

```powershell
Invoke-WebRequest -Uri "https://syno-cast.vercel.app/health" -UseBasicParsing | Select-Object -ExpandProperty Content
```

Then I can give you the exact fix! 🎯
