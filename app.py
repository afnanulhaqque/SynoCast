import os
import sqlite3
import requests
import random
import resend
import concurrent.futures
from flask import Flask, render_template, request, session, jsonify, abort, redirect, url_for
from pywebpush import webpush, WebPushException
import json
from datetime import datetime, timedelta, timezone
from google import genai
import threading
import time
from dotenv import load_dotenv
from jinja2.exceptions import TemplateSyntaxError
import utils
from database import get_db, init_db
from extensions import csrf, limiter, talisman
from routes.main import main_bp
from routes.api import api_bp
from routes.auth import auth_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_key_123")
app.config['SESSION_TYPE'] = 'filesystem'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Init Extensions
csrf.init_app(app)
limiter.init_app(app)

# Talisman Config
csp = {
    'default-src': ["'self'", "https://*.googleapis.com"],
    'script-src': ["'self'", "'unsafe-inline'", "https://*.googleapis.com", 
                   "https://*.gstatic.com", "https://maps.googleapis.com", 
                   "https://unpkg.com", "https://cdnjs.cloudflare.com",
                   "https://cdn.jsdelivr.net"],
    'style-src': ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com", 
                  "https://unpkg.com", "https://cdnjs.cloudflare.com",
                  "https://cdn.jsdelivr.net"],
    'img-src': ["'self'", "data:", "https://*.openweathermap.org", 
                "https://tile.openstreetmap.org", "https://*.unsplash.com", 
                "https://flagcdn.com", "https://*.ggpht.com",
                "https://openweathermap.org"],
    'connect-src': ["'self'", "https://api.openweathermap.org", 
                    "https://nominatim.openstreetmap.org", 
                    "https://countriesnow.space",
                    "https://api.exchangerate-api.com",
                    "https://generativelanguage.googleapis.com",
                    "https://ip-api.com"],
    'font-src': ["'self'", "https://fonts.gstatic.com", "https://cdnjs.cloudflare.com"]
}

if not os.environ.get("VERCEL"):
    talisman.init_app(app, content_security_policy=csp, force_https=False)
else:
    talisman.init_app(app, content_security_policy=csp)

# Global Keys
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY")
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY")
VAPID_CLAIMS = {
    "sub": f"mailto:{os.environ.get('REPLY_TO_EMAIL', 'support@synocast.app')}"
}

# Database Init
try:
    init_db()
except Exception as e:
    app.logger.error(f"Database initialization failed: {e}")

# Register Blueprints
app.register_blueprint(main_bp)
app.register_blueprint(api_bp)
app.register_blueprint(auth_bp)

# Upload Folder Setup
UPLOAD_FOLDER = os.path.join('assets', 'user_uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
if not os.environ.get("VERCEL"):
    try:
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
    except Exception as e:
         app.logger.warning(f"Could not create upload folder: {e}")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Background Tasks ---

def send_push_notification(subscription_info, message_body):
    """Helper to send web push"""
    try:
        webpush(
            subscription_info=subscription_info,
            data=message_body,
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
        return True
    except WebPushException as ex:
        app.logger.error(f"WebPush Error: {ex}")
        return False
    except Exception as e:
        app.logger.error(f"Push Error: {e}")
        return False

def check_weather_alerts():
    """Background task to check for severe weather alerts for all subscribers."""
    with app.app_context():
        while True:
            try:
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT s.email, s.lat, s.lon, up.alert_thresholds 
                        FROM subscriptions s 
                        LEFT JOIN user_preferences up ON s.email = up.email 
                        WHERE s.lat IS NOT NULL
                    """)
                    subscribers = cursor.fetchall()
                
                active_alerts_cache = {} 

                for email, lat, lon, prefs_json in subscribers:
                    prefs = {"types": ["severe", "rain", "temp", "air"], "severity": "medium"}
                    if prefs_json:
                        try:
                             loaded = json.loads(prefs_json)
                             if isinstance(loaded, dict):
                                 prefs = loaded
                        except:
                            pass
                    
                    loc_key = f"{round(lat, 1)},{round(lon, 1)}"
                    
                    alerts = []
                    if loc_key in active_alerts_cache:
                        alerts = active_alerts_cache[loc_key]
                    else:
                        alert_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly,daily&appid={OPENWEATHER_API_KEY}"
                        try:
                            res = requests.get(alert_url, timeout=5)
                            if res.ok:
                                alerts = res.json().get('alerts', [])
                                active_alerts_cache[loc_key] = alerts
                        except Exception as e:
                            app.logger.warning(f"Failed to fetch alerts for {email}: {e}")

                    if not alerts:
                        continue

                    for alert in alerts:
                        event_lower = alert.get('event', '').lower()
                        desc_lower = alert.get('description', '').lower()
                        
                        user_types = prefs.get("types", [])
                        is_relevant = False
                        
                        keyword_map = {
                            "severe": ["tornado", "hurricane", "thunderstorm", "warning", "danger", "severe"],
                            "rain": ["rain", "flood", "shower", "storm"],
                            "temp": ["heat", "cold", "freeze", "frost", "advisory"],
                            "air": ["air quality", "pollution", "smoke", "fire"]
                        }
                        
                        if not user_types:
                             continue

                        for t in user_types:
                            keywords = keyword_map.get(t, [])
                            if any(k in event_lower for k in keywords) or any(k in desc_lower for k in keywords):
                                is_relevant = True
                                break
                        
                        if not is_relevant:
                            continue

                        advice = "Stay safe and follow local authorities."
                        gemini_key = os.environ.get("GEMINI_API_KEY")
                        if gemini_key:
                            try:
                                client = genai.Client(api_key=gemini_key.strip())
                                prompt = f"Serious weather alert: {alert['event']}. Description: {alert['description']}. Provide 1-2 sentences of actionable, specific advice for someone in this area (e.g., 'consider parking your car in a covered area')."
                                response = client.models.generate_content(
                                    model="gemini-2.0-flash-exp",
                                    contents=prompt
                                )
                                advice = response.text if response.text else advice
                            except:
                                pass

                        try:
                            resend.Emails.send({
                                "from": "SynoCast Alerts <onboarding@resend.dev>",
                                "to": email,
                                "subject": f"⚠️ {alert['event']}",
                                "html": f"""
                                    <div style="font-family: sans-serif; padding: 20px; border: 2px solid #dc3545; border-radius: 10px;">
                                        <h2 style="color: #dc3545; margin-top: 0;">{alert['event']}</h2>
                                        <p>{alert['description']}</p>
                                        <div style="background: #f8d7da; padding: 15px; border-radius: 5px; color: #721c24; font-weight: bold;">
                                            <i class="fas fa-robot"></i> SynoCast AI Advice: {advice}
                                        </div>
                                        <p style="margin-top: 20px; font-size: 12px; color: #888;">
                                            You received this because you subscribed to '{", ".join(user_types)}' alerts.
                                            <a href="https://syno-cast.vercel.app/subscribe">Update Preferences</a>
                                        </p>
                                    </div>
                                """
                            })
                            app.logger.info(f"Sent alert '{alert['event']}' to {email}")
                        except Exception as e:
                             app.logger.error(f"Failed to send alert email: {e}")

                time.sleep(3600) 
            except Exception as e:
                app.logger.error(f"Weather alert background task error: {e}")
                time.sleep(60)

def trigger_daily_forecast_webhooks():
    """Background task to trigger daily forecast webhooks."""
    with app.app_context():
        while True:
            try:
                with get_db() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, webhook_url, event_types, lat, lon, secret_token, last_triggered
                        FROM webhook_subscriptions
                        WHERE is_active = 1
                    """)
                    subscriptions = cursor.fetchall()
                
                for sub in subscriptions:
                    try:
                        event_types = json.loads(sub['event_types'])
                        if 'daily_forecast' not in event_types:
                            continue
                            
                        should_send = False
                        if not sub['last_triggered']:
                            should_send = True
                        else:
                            try:
                                last_iso = sub['last_triggered'].replace('Z', '+00:00')
                                last = datetime.fromisoformat(last_iso)
                                if (datetime.utcnow().replace(tzinfo=timezone.utc) - last).total_seconds() > 72000:
                                    should_send = True
                            except:
                                should_send = True
                        
                        if should_send:
                            api_key = os.environ.get("OPENWEATHER_API_KEY")
                            if not api_key:
                                app.logger.error("OPENWEATHER_API_KEY not set")
                                break
                                
                            weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={sub['lat']}&lon={sub['lon']}&units=metric&appid={api_key}"
                            res = requests.get(weather_url, timeout=10)
                            if not res.ok:
                                continue
                                
                            data = res.json()
                            
                            payload = {
                                "event_type": "daily_forecast",
                                "location": {
                                    "city": data.get("name"),
                                    "lat": sub['lat'],
                                    "lon": sub['lon']
                                },
                                "forecast": {
                                    "temp": data["main"]["temp"],
                                    "condition": data["weather"][0]["description"],
                                    "high": data["main"]["temp_max"],
                                    "low": data["main"]["temp_min"]
                                },
                                "timestamp": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
                            }
                            
                            success, error = utils.send_webhook(sub['webhook_url'], payload, sub['secret_token'])
                            
                            with get_db() as conn:
                                if success:
                                    conn.execute("UPDATE webhook_subscriptions SET last_triggered = ?, failure_count = 0 WHERE id = ?", 
                                                (datetime.utcnow().isoformat() + "Z", sub['id']))
                                else:
                                    conn.execute("UPDATE webhook_subscriptions SET failure_count = failure_count + 1 WHERE id = ?", 
                                                (sub['id'],))
                                conn.commit()
                                
                    except Exception as sub_e:
                        app.logger.error(f"Error processing subscription {sub['id']}: {sub_e}")
                        continue

                time.sleep(300)
                
            except Exception as e:
                app.logger.error(f"Daily forecast webhook task error: {e}")
                time.sleep(60)

# --- Error Handlers ---

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", date_time_info=utils.get_local_time_string(), active_page="404"), 404

@app.errorhandler(500)
def internal_error(e):
    if request.path.startswith('/api/'):
        return jsonify({"error": "Internal server error occurred"}), 500
    return render_template("500.html", date_time_info=utils.get_local_time_string(), active_page="404"), 500

@app.errorhandler(TemplateSyntaxError)
def syntax_error(e):
    return render_template("syntax_error.html", date_time_info=utils.get_local_time_string()), 500

@app.errorhandler(Exception)
def unhandled_exception(e):
    app.logger.error(f"Unhandled Exception: {e}")
    if "Too Many Requests" in str(e) or (hasattr(e, 'code') and e.code == 429):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Rate limit exceeded. Please slow down."}), 429
        return render_template("500.html", message="Too many requests. Please try again later.", date_time_info=utils.get_local_time_string(), active_page="404"), 429

    if request.path.startswith('/api/'):
        if "API_KEY_INVALID" in str(e):
            return jsonify({"error": "Invalid API Key for AI service"}), 500
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    return render_template("500.html", date_time_info=utils.get_local_time_string(), active_page="404"), 500

if __name__ == "__main__":
    if not os.environ.get("VERCEL"):
        # Start background threads
        alert_thread = threading.Thread(target=check_weather_alerts, daemon=True)
        alert_thread.start()
        
        daily_thread = threading.Thread(target=trigger_daily_forecast_webhooks, daemon=True)
        daily_thread.start()
        
    app.run(debug=True)