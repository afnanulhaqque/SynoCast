# 🚨 URGENT FIX: Your Vercel Deployment is Missing VAPID Keys

## ⚡ The Problem

Your Vercel deployment is crashing because it's missing **VAPID keys** for push notifications.

**Current status:**

- ✅ You have: `FLASK_SECRET_KEY`, `OPENWEATHER_API_KEY`, `RESEND_API_KEY`, `GEMINI_API_KEY`, `NEWS_API_KEY`
- ❌ You're missing: `VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY`

---

## 🔧 Step 1: Generate VAPID Keys

Run this command in PowerShell to generate new VAPID keys:

```powershell
cd d:\SynoCast
.\.venv\Scripts\python.exe gen_keys_v2.py
```

**You'll see output like:**

```
VAPID_PRIVATE_KEY=abc123xyz...
VAPID_PUBLIC_KEY=ABC456XYZ...
```

**IMPORTANT:** Copy both values - you'll need them in the next step!

---

## 🌐 Step 2: Add VAPID Keys to Vercel

### Go to Vercel Dashboard:

1. **Open:** https://vercel.com/dashboard
2. **Click:** Your "syno-cast" project
3. **Click:** "Settings" tab (top navigation)
4. **Click:** "Environment Variables" (left sidebar)

### Add VAPID_PRIVATE_KEY:

1. **Click:** "Add New" button
2. **Name:** `VAPID_PRIVATE_KEY`
3. **Value:** Paste the value from Step 1 (starts with lowercase letters/numbers)
4. **Environments:** Check ALL three boxes:
   - ✓ Production
   - ✓ Preview
   - ✓ Development
5. **Click:** "Save"

### Add VAPID_PUBLIC_KEY:

1. **Click:** "Add New" button again
2. **Name:** `VAPID_PUBLIC_KEY`
3. **Value:** Paste the value from Step 1 (starts with uppercase 'B')
4. **Environments:** Check ALL three boxes:
   - ✓ Production
   - ✓ Preview
   - ✓ Development
5. **Click:** "Save"

---

## 🔄 Step 3: Redeploy

**CRITICAL:** Environment variables only apply to NEW deployments!

1. **Click:** "Deployments" tab (top navigation)
2. **Find:** The most recent deployment (top of the list)
3. **Click:** The three dots menu (⋯) on the right
4. **Click:** "Redeploy"
5. **Confirm:** Click "Redeploy" in the popup
6. **Wait:** 1-2 minutes for deployment to complete

---

## ✅ Step 4: Verify It Works

After redeployment completes:

1. **Visit:** https://syno-cast.vercel.app/
2. **You should see:** Your SynoCast homepage (not an error!)

If you still see an error:

1. **Visit:** https://syno-cast.vercel.app/health
2. **Check:** All environment variables should show `true`
3. **If any show `false`:** Go back to Step 2 and add the missing variable

---

## 📝 Step 5: Update Your Local .env File (Optional but Recommended)

Add the VAPID keys to your local `.env` file so you have them for future reference:

```powershell
# Open .env file in notepad
notepad d:\SynoCast\.env
```

Add these two lines at the end (using the values from Step 1):

```
VAPID_PRIVATE_KEY=your_private_key_here
VAPID_PUBLIC_KEY=your_public_key_here
```

Save and close.

---

## 🎯 Quick Checklist

- [ ] Generate VAPID keys using `gen_keys_v2.py`
- [ ] Copy both VAPID_PRIVATE_KEY and VAPID_PUBLIC_KEY values
- [ ] Add VAPID_PRIVATE_KEY to Vercel (all 3 environments)
- [ ] Add VAPID_PUBLIC_KEY to Vercel (all 3 environments)
- [ ] Redeploy from Vercel dashboard
- [ ] Wait 2 minutes
- [ ] Test: https://syno-cast.vercel.app/
- [ ] (Optional) Add keys to local .env file

---

## 🔍 Verify All Environment Variables

Your Vercel should have these **7 environment variables**:

1. ✓ `FLASK_SECRET_KEY`
2. ✓ `OPENWEATHER_API_KEY`
3. ✓ `RESEND_API_KEY`
4. ✓ `GEMINI_API_KEY`
5. ✓ `NEWS_API_KEY`
6. ✓ `VAPID_PRIVATE_KEY` ← **ADD THIS**
7. ✓ `VAPID_PUBLIC_KEY` ← **ADD THIS**

---

## 💡 Why This Happened

Your app uses push notifications, which require VAPID keys for security. The app tries to load these keys on startup:

```python
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY")
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY")
```

When these are missing, the serverless function crashes with:

```
FUNCTION_INVOCATION_FAILED
```

---

## 🚫 What to Ignore

These are **NOT** the problem (they're just Vercel's internal warnings):

- ❌ Zustand deprecation warnings
- ❌ `instrument.js` warnings
- ❌ Favicon 500 error (will fix itself)

**Only focus on:** Adding the VAPID keys!

---

## 🆘 Still Having Issues?

If it still doesn't work after following all steps:

1. **Check Vercel logs:**

   - Dashboard → syno-cast → Deployments → Latest → Functions → /api/index
   - Copy the error message

2. **Check the health endpoint:**

   - Visit: https://syno-cast.vercel.app/health
   - Screenshot the output

3. **Send me:**
   - The error from Vercel logs
   - Screenshot of /health endpoint
   - Confirmation that all 7 environment variables are set

---

## 🎉 Expected Result

After completing these steps, you should see:

✅ **Homepage loads:** https://syno-cast.vercel.app/  
✅ **Health check passes:** https://syno-cast.vercel.app/health shows all `true`  
✅ **No more 500 errors!**

---

**Let me know once you've added the VAPID keys and redeployed!** 🚀
