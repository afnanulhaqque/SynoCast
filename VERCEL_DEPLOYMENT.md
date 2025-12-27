# Vercel Deployment Guide for SynoCast

## Issues Fixed ✅

1. **Missing Dependency**: Added `pywebpush` to `requirements.txt`
2. **Incorrect Vercel Config**: Updated `vercel.json` to use proper Python/Flask structure
3. **Entry Point**: Created `api/index.py` as the Vercel entry point

## Required Environment Variables

Make sure these are set in your Vercel project settings:

### Required (App won't work without these):

- `FLASK_SECRET_KEY` - Secret key for Flask sessions
- `OPENWEATHER_API_KEY` - OpenWeatherMap API key
- `RESEND_API_KEY` - Resend email service API key
- `GEMINI_API_KEY` - Google Gemini AI API key
- `NEWS_API_KEY` - News API key
- `VAPID_PRIVATE_KEY` - VAPID private key for push notifications
- `VAPID_PUBLIC_KEY` - VAPID public key for push notifications

### Optional:

- `REPLY_TO_EMAIL` - Reply-to email address (defaults to admin@synocast.app)

## Deployment Steps

### 1. Push your changes to Git

```bash
git add .
git commit -m "Fix Vercel deployment configuration"
git push
```

### 2. Set Environment Variables in Vercel Dashboard

Go to your Vercel project → Settings → Environment Variables and add all the required variables listed above.

**Important**: Copy the values from your local `.env` file.

### 3. Deploy

Option A - Automatic (if connected to Git):

- Vercel will automatically deploy when you push to your main branch

Option B - Manual via Vercel CLI:

```bash
vercel --prod
```

## Common Issues & Solutions

### Issue: "Build failed"

**Solution**: Check Vercel build logs for missing dependencies or syntax errors

### Issue: "Internal Server Error (500)" or "FUNCTION_INVOCATION_FAILED"

**Solution**:

- **Check Vercel Function Logs**: Go to your Vercel project → Deployments → Click on your deployment → Functions tab → Click on any failed function to see detailed error logs
- Check that all environment variables are set correctly in Vercel (Settings → Environment Variables)
- Common causes:
  - Missing environment variables (FLASK_SECRET_KEY, API keys, etc.)
  - Import errors (missing dependencies in requirements.txt)
  - File path issues (use absolute paths, not relative)
  - Database initialization errors on read-only filesystem

**How to check logs**:

```bash
# Using Vercel CLI
vercel logs <deployment-url>

# Or check in Vercel Dashboard:
# Project → Deployments → [Your Deployment] → Functions → View Logs
```

### Issue: "Database errors"

**Solution**:

- The app uses SQLite which works on Vercel but data is ephemeral
- Consider migrating to a persistent database like PostgreSQL for production
- Database file is stored in `/tmp` on Vercel and will be cleared periodically

### Issue: "Static files not loading"

**Solution**:

- Ensure `assets` folder structure is correct
- Check that paths in templates use `url_for('static', filename='...')`
- Verify files exist in the correct directories

### Issue: "Background tasks not running"

**Solution**:

- Background threads (like weather alerts) are disabled on Vercel
- Use Vercel Cron Jobs or external services like Upstash QStash for scheduled tasks

## Testing Your Deployment

After deployment:

1. Visit your Vercel URL
2. Check browser console for errors
3. Test weather API endpoints
4. Verify push notifications work
5. Test email subscription

## Database Considerations

⚠️ **Important**: Vercel uses ephemeral storage (`/tmp`). Your SQLite database will be reset on each deployment and may be cleared during function cold starts.

**Recommended Solutions**:

1. Use Vercel Postgres
2. Use external database (Supabase, PlanetScale, etc.)
3. Use Vercel KV for simple key-value storage

## Performance Tips

1. **Caching**: The app already implements weather data caching (10 min)
2. **Rate Limiting**: Flask-Limiter is configured for API protection
3. **CDN**: Vercel automatically serves static files via CDN

## Next Steps

- [ ] Deploy to Vercel
- [ ] Test all features
- [ ] Set up custom domain (optional)
- [ ] Configure database persistence
- [ ] Set up monitoring/logging
