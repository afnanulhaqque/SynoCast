# URGENT: Steps to Fix 500 Error

## The Problem

Your app is getting a 500 Internal Server Error. This means the Python backend is crashing.
The Zustand warnings are NOT the issue - they're harmless JavaScript warnings from Vercel's monitoring.

## STEP 1: Push Latest Changes (Do This First!)

```bash
git add .
git commit -m "Add health check and improve error handling"
git push
```

Wait for Vercel to redeploy (usually 1-2 minutes).

## STEP 2: Test the Health Endpoint

After deployment completes, visit:
https://syno-cast.vercel.app/health

### If you see JSON like this - GOOD!

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

### If you see an error or any "false" values:

- Go to Vercel Dashboard → syno-cast → Settings → Environment Variables
- Add the missing variables
- Click "Redeploy" button

## STEP 3: Check Vercel Logs (MOST IMPORTANT!)

### Method A: Vercel Dashboard (Easiest)

1. Go to https://vercel.com/dashboard
2. Click on "syno-cast" project
3. Click "Deployments" tab
4. Click on the most recent deployment
5. Scroll down to "Functions" section
6. Click on "/api/index"
7. Look for RED error messages
8. **COPY THE ENTIRE ERROR MESSAGE AND SEND IT TO ME**

### Method B: Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# View logs
vercel logs https://syno-cast.vercel.app --follow
```

## STEP 4: Most Common Issues

### Issue 1: Missing Environment Variables (90% of cases)

**Symptoms**: Health endpoint shows "false" for some variables

**Fix**:

1. Go to Vercel Dashboard → syno-cast → Settings → Environment Variables
2. Add ALL of these (copy from your .env file):
   - FLASK_SECRET_KEY
   - OPENWEATHER_API_KEY
   - RESEND_API_KEY
   - GEMINI_API_KEY
   - NEWS_API_KEY
   - VAPID_PRIVATE_KEY
   - VAPID_PUBLIC_KEY
3. Click "Redeploy" button (important!)

### Issue 2: Import Error

**Symptoms**: Logs show "ModuleNotFoundError" or "ImportError"

**Fix**:

- Check the exact module name in the error
- Add it to requirements.txt
- Push and redeploy

### Issue 3: File Path Issues

**Symptoms**: Logs show "FileNotFoundError"

**Fix**:

- Check which file is missing
- Verify it exists in your repo
- Check .gitignore isn't excluding it

## WHAT TO SEND ME

After checking the logs, send me:

1. **The exact error message from Vercel logs** (copy/paste the full error)
2. **Screenshot of the /health endpoint** (if it loads)
3. **List of environment variables you have set** (just the names, not values)

Then I can give you the exact fix!

## Quick Test Commands

```bash
# Test health endpoint
curl https://syno-cast.vercel.app/health

# Or open in browser:
# https://syno-cast.vercel.app/health
```

## Remember

- Zustand warnings = IGNORE (not the problem)
- 500 error = Backend crash (need to see logs)
- After adding env vars = MUST redeploy
- Health endpoint = Quick way to check if app loads
