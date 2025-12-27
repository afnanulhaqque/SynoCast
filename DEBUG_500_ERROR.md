# How to Debug Vercel 500 Error

## Step 1: Check Vercel Function Logs

### Via Vercel Dashboard:

1. Go to https://vercel.com/dashboard
2. Click on your "syno-cast" project
3. Click on "Deployments" tab
4. Click on the most recent deployment
5. Click on "Functions" tab
6. You should see `/api/index` function - click on it
7. Look for error messages in the logs

### Via Vercel CLI (Faster):

```bash
# Install Vercel CLI if you haven't
npm i -g vercel

# Login
vercel login

# View logs (replace with your actual deployment URL)
vercel logs https://syno-cast.vercel.app
```

## Step 2: Common Issues to Check

### A. Missing Environment Variables

The most common cause of 500 errors. Check if ALL these are set in Vercel:

**Go to**: Vercel Dashboard → syno-cast → Settings → Environment Variables

Required variables:

- [ ] FLASK_SECRET_KEY
- [ ] OPENWEATHER_API_KEY
- [ ] RESEND_API_KEY
- [ ] GEMINI_API_KEY
- [ ] NEWS_API_KEY
- [ ] VAPID_PRIVATE_KEY
- [ ] VAPID_PUBLIC_KEY

**Important**: After adding environment variables, you MUST redeploy!

### B. Import Errors

Check if all dependencies are installed. The logs will show something like:

```
ModuleNotFoundError: No module named 'xyz'
```

### C. Database Issues

SQLite might fail to initialize on Vercel. Check logs for:

```
sqlite3.OperationalError: unable to open database file
```

## Step 3: Quick Fix - Add Debug Endpoint

Let me create a simple health check endpoint to test if the app is loading.

## Step 4: What to Look For in Logs

Common error patterns:

### Pattern 1: Missing Environment Variable

```
KeyError: 'FLASK_SECRET_KEY'
```

**Fix**: Add the missing variable in Vercel dashboard

### Pattern 2: Import Error

```
ModuleNotFoundError: No module named 'pywebpush'
```

**Fix**: Add to requirements.txt and redeploy

### Pattern 3: File Not Found

```
FileNotFoundError: [Errno 2] No such file or directory: 'sw.js'
```

**Fix**: Check file paths are correct

### Pattern 4: Database Error

```
sqlite3.OperationalError: unable to open database file
```

**Fix**: This is expected on first run, should auto-create

## Step 5: Test Locally with Vercel Environment

```bash
# Set VERCEL=1 to simulate Vercel environment
$env:VERCEL="1"

# Run the test script
.\.venv\Scripts\python.exe test_vercel_deploy.py

# Run the app
.\.venv\Scripts\python.exe -m flask run
```

## Next Steps

1. **Check the logs** using one of the methods above
2. **Copy the exact error message** and share it
3. I'll help you fix the specific issue

The logs will tell us exactly what's wrong!
