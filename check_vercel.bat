@echo off
echo ========================================
echo Vercel Deployment Checker
echo ========================================
echo.

echo Step 1: Testing health endpoint...
echo.
curl -s https://syno-cast.vercel.app/health
echo.
echo.

echo ========================================
echo If you see JSON above with "status": "ok", the app is loading!
echo.
echo If you see an error, check:
echo 1. Vercel Dashboard -^> syno-cast -^> Settings -^> Environment Variables
echo 2. Make sure ALL required variables are set
echo 3. Redeploy after adding variables
echo.
echo To view detailed logs:
echo   vercel logs https://syno-cast.vercel.app
echo.
echo Or check in Vercel Dashboard:
echo   Deployments -^> Latest -^> Functions -^> View Logs
echo ========================================
pause
