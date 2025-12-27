# 🚨 CRITICAL: Your Serverless Function is Crashing on Startup

## What's Happening

Your Vercel deployment shows:

```
FUNCTION_INVOCATION_FAILED
This Serverless Function has crashed.
```

This means the Python function is **failing to start** - it's not even getting to run your code. This is almost always caused by:

1. **Missing environment variables** (95% of cases)
2. **Import errors** (missing dependencies)
3. **Syntax errors** in the code

---

## 🔍 Step 1: Check Vercel Logs (REQUIRED)

You **MUST** check the Vercel logs to see the actual error. Here are 3 ways:

### Method A: Vercel Dashboard (Recommended - Shows Full Error)

1. **Go to:** https://vercel.com/dashboard
2. **Click:** Your "syno-cast" project
3. **Click:** "Deployments" tab
4. **Click:** The most recent deployment (top of list)
5. **Scroll down** to "Build Logs" section
6. **Look for RED errors** - especially near the bottom
7. **Copy the entire error message**

### Method B: Check Function Logs

1. On the same deployment page
2. **Scroll to:** "Functions" section
3. **Click:** "/api/index"
4. **Look for:** Runtime errors
5. **Copy any error messages**

### Method C: Use Vercel CLI (Advanced)

```powershell
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Link to your project
cd d:\SynoCast
vercel link

# View real-time logs
vercel logs --follow
```

---

## 🎯 Step 2: Most Likely Fix - Environment Variables

Since your function is crashing immediately, it's almost certainly **missing environment variables**.

### Check Your Vercel Environment Variables:

1. **Go to:** https://vercel.com/dashboard
2. **Click:** "syno-cast" project
3. **Click:** "Settings" → "Environment Variables"
4. **Verify these 7 variables exist:**

```
✓ FLASK_SECRET_KEY
✓ OPENWEATHER_API_KEY
✓ RESEND_API_KEY
✓ GEMINI_API_KEY
✓ NEWS_API_KEY
✓ VAPID_PRIVATE_KEY
✓ VAPID_PUBLIC_KEY
```

### If ANY are missing:

1. **Click:** "Add New" button
2. **Name:** Enter the variable name (e.g., `FLASK_SECRET_KEY`)
3. **Value:** Copy from your `.env` file
4. **Environments:** Select ALL three:
   - ✓ Production
   - ✓ Preview
   - ✓ Development
5. **Click:** "Save"
6. **Repeat** for all missing variables

### ⚠️ CRITICAL: After Adding Variables

**You MUST redeploy!** Environment variables only apply to NEW deployments.

1. **Go to:** "Deployments" tab
2. **Find:** Latest deployment
3. **Click:** Three dots menu (⋯)
4. **Click:** "Redeploy"
5. **Wait:** 1-2 minutes for deployment to complete
6. **Test:** Visit https://syno-cast.vercel.app/

---

## 🔧 Step 3: Check Your Local .env File

Let me help you verify what environment variables you have locally:

```powershell
# Run this in PowerShell to see your .env variables (without showing values)
Get-Content d:\SynoCast\.env | Where-Object { $_ -match '=' } | ForEach-Object { ($_ -split '=')[0] }
```

This will show you the variable names you need to add to Vercel.

---

## 📋 Step 4: What to Send Me

After checking the above, please share:

### Option 1: If you found the error in logs

```
Copy/paste the exact error from Vercel logs here
```

### Option 2: If you can't access logs

Tell me:

1. How many environment variables do you have set in Vercel?
2. Which ones are you missing from this list:
   - FLASK_SECRET_KEY
   - OPENWEATHER_API_KEY
   - RESEND_API_KEY
   - GEMINI_API_KEY
   - NEWS_API_KEY
   - VAPID_PRIVATE_KEY
   - VAPID_PUBLIC_KEY

---

## 🚀 Quick Fix Checklist

Try this in order:

- [ ] Check Vercel environment variables
- [ ] Add any missing variables from the list above
- [ ] Make sure to select ALL environments (Production, Preview, Development)
- [ ] Click "Redeploy" on the latest deployment
- [ ] Wait 2 minutes
- [ ] Test: https://syno-cast.vercel.app/

If it still fails after this, check the Vercel logs and send me the error!

---

## 💡 Common Error Messages and Fixes

### Error: `KeyError: 'FLASK_SECRET_KEY'`

**Fix:** Add `FLASK_SECRET_KEY` to Vercel environment variables

### Error: `ModuleNotFoundError: No module named 'xyz'`

**Fix:** Add the missing module to `requirements.txt` and push

### Error: `ImportError: cannot import name 'xyz'`

**Fix:** Check if there's a typo in your imports in `app.py`

### Error: `sqlite3.OperationalError`

**Fix:** This is usually OK - the database will be created on first run

---

## 🎯 Next Steps

1. **Check Vercel environment variables** (most likely issue)
2. **Add missing variables** if any
3. **Redeploy**
4. **If still failing:** Check Vercel logs and send me the error

The logs will tell us exactly what's wrong! 🔍
