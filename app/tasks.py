import os
import requests
import json
import sqlite3
import time
import threading
from datetime import datetime, timezone
from google import genai
import resend
from pywebpush import webpush, WebPushException
from .database import get_db
from . import utils

# Keys
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY")
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY")
VAPID_CLAIMS = {
    "sub": f"mailto:{os.environ.get('REPLY_TO_EMAIL', 'support@synocast.app')}"
}

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
        print(f"WebPush Error: {ex}")
        return False
    except Exception as e:
        print(f"Push Error: {e}")
        return False

def check_weather_alerts(app):
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
                            # Using print or basic logger if app logger not fully avail in thread without context 
                            # (but we are in app_context)
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

def trigger_daily_forecast_webhooks(app):
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
                            # Re-fetch key if needed or use global
                            api_key = os.environ.get("OPENWEATHER_API_KEY")
                            if not api_key:
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
