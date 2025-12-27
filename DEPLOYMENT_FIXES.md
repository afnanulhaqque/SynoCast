# Vercel Deployment Fixes - Summary

## Issues Fixed ✅

### 1. **Missing `pywebpush` dependency**

- **Problem**: App imports `pywebpush` but it wasn't in `requirements.txt`
- **Fix**: Added `pywebpush` to `requirements.txt`
- **File**: `requirements.txt`

### 2. **Incorrect Vercel Configuration**

- **Problem**: `vercel.json` was using wrong format for Python/Flask apps
- **Fix**: Updated to use proper `@vercel/python` builder with `api/index.py` entry point
- **Files**: `vercel.json`, `api/index.py`

### 3. **Upload Folder Creation on Read-Only Filesystem**

- **Problem**: App tried to create `assets/user_uploads` folder on Vercel's read-only filesystem
- **Fix**: Wrapped folder creation in try-except and skip on Vercel
- **File**: `app.py` (lines 399-407)

### 4. **Background Thread in Serverless Environment**

- **Problem**: Weather alerts background thread can't run on Vercel's serverless platform
- **Fix**: Disabled background thread when `VERCEL` environment variable is set
- **File**: `app.py` (lines 1997-2002)

### 5. **Static File Serving Issues**

- **Problem**: `sw.js`, `robots.txt`, `sitemap.xml` weren't being served correctly
- **Fix**: Updated routes to use `send_from_directory` instead of `send_static_file`
- **File**: `app.py` (lines 417-431)

### 6. **Better Error Handling for Vercel**

- **Problem**: No detailed error logging for deployment failures
- **Fix**: Added comprehensive error handling in `api/index.py` with traceback logging
- **File**: `api/index.py`

## Files Modified

1. ✏️ `requirements.txt` - Added `pywebpush`
2. ✏️ `vercel.json` - Fixed configuration for Python/Flask
3. ➕ `api/index.py` - Created Vercel entry point with error handling
4. ✏️ `app.py` - Multiple fixes:
   - Upload folder creation (lines 399-407)
   - Background thread handling (lines 1997-2002)
   - Static file routes (lines 417-431)
5. ✏️ `VERCEL_DEPLOYMENT.md` - Updated with troubleshooting guide
6. ➕ `test_vercel_deploy.py` - Created local testing script

## Next Steps

### 1. Commit and Push Changes

```bash
git add .
git commit -m "Fix Vercel deployment issues"
git push
```

### 2. Verify Environment Variables in Vercel

Go to Vercel Dashboard → Your Project → Settings → Environment Variables

**Required variables**:

- `FLASK_SECRET_KEY`
- `OPENWEATHER_API_KEY`
- `RESEND_API_KEY`
- `GEMINI_API_KEY`
- `NEWS_API_KEY`
- `VAPID_PRIVATE_KEY`
- `VAPID_PUBLIC_KEY`
- `REPLY_TO_EMAIL` (optional)

### 3. Check Deployment Logs

If deployment still fails:

**Via Vercel Dashboard**:

1. Go to your project on Vercel
2. Click on "Deployments"
3. Click on the failed deployment
4. Click on "Functions" tab
5. Click on any function to see detailed error logs

**Via Vercel CLI**:

```bash
vercel logs <your-deployment-url>
```

### 4. Test Locally First

Before deploying, run the test script:

```bash
.\.venv\Scripts\python.exe test_vercel_deploy.py
```

This will catch any import or initialization errors before deployment.

## About the Zustand Warning

The Zustand deprecation warning you saw is just a warning, not an error. It won't cause the deployment to fail. It's likely coming from a CDN-loaded library and can be safely ignored for now. If you want to fix it later, you'd need to:

1. Find where Zustand is being imported (likely in a `<script>` tag)
2. Update the import to use: `import { create } from 'zustand'` instead of the default export

But this is low priority - focus on fixing the 500 error first.

## Important Notes

### Database Persistence

⚠️ Your SQLite database on Vercel is **ephemeral**:

- Stored in `/tmp` directory
- Cleared on each deployment
- May be cleared during cold starts
- Not suitable for production data

**Recommended solutions**:

- Vercel Postgres (native integration)
- Supabase (free tier available)
- PlanetScale (MySQL-compatible)
- Neon (Postgres)

### Background Tasks

⚠️ Weather alerts background thread is **disabled on Vercel**:

- Serverless functions don't support long-running background tasks
- Use Vercel Cron Jobs for scheduled tasks
- Or use external services like Upstash QStash

### File Uploads

⚠️ File uploads to `assets/user_uploads` **won't persist on Vercel**:

- Read-only filesystem except `/tmp`
- Use cloud storage instead:
  - Vercel Blob Storage
  - AWS S3
  - Cloudinary
  - Uploadcare

## Testing Checklist

After deployment, test these features:

- [ ] Homepage loads correctly
- [ ] Weather data displays
- [ ] News articles load
- [ ] User login/signup works
- [ ] Favorite locations can be saved
- [ ] Profile page accessible
- [ ] API endpoints respond correctly
- [ ] Static files (CSS, JS, images) load
- [ ] Service worker registers

## Support

If you're still getting 500 errors after these fixes:

1. Check the Vercel function logs (instructions above)
2. Look for specific error messages
3. Verify all environment variables are set
4. Run `test_vercel_deploy.py` locally to catch issues early
