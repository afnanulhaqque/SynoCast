import os
import json
import time
import requests
import sqlite3
from datetime import datetime, timedelta, timezone
from pywebpush import webpush, WebPushException
from app.database import get_db
import app.utils as utils

def send_push_notification(subscription_info, message_body, vapid_private_key, vapid_claims):
    """Helper to send web push"""
    try:
        webpush(
            subscription_info=subscription_info,
            data=message_body,
            vapid_private_key=vapid_private_key,
            vapid_claims=vapid_claims
        )
        return True
    except WebPushException as ex:
        print(f"WebPush Error: {ex}")
        return False
    except Exception as e:
        print(f"Push Error: {e}")
        return False

def check_weather_alerts(app_context):
    """Background task to check for severe weather alerts for all subscribers."""
    with app_context:
        OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
        VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY")
        VAPID_CLAIMS = {
            "sub": f"mailto:{os.environ.get('REPLY_TO_EMAIL', 'support@synocast.app')}"
        }
        
        while True:
            try:
                # 1. Handle Email Subscribers
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT s.email, s.lat, s.lon, up.alert_thresholds 
                        FROM subscriptions s 
                        LEFT JOIN user_preferences up ON s.email = up.email 
                        WHERE s.lat IS NOT NULL
                    """)
                    email_subscribers = cursor.fetchall()
                    
                    # 2. Handle Push Subscribers
                    cursor.execute("SELECT endpoint, p256dh, auth, lat, lon FROM push_subscriptions WHERE lat IS NOT NULL")
                    push_subscribers = cursor.fetchall()
                
                # Cache alerts by location to avoid rate limits
                active_alerts_cache = {}
                locations = set()
                for _, lat, lon, _ in email_subscribers:
                    locations.add((round(lat, 1), round(lon, 1)))
                for _, _, _, lat, lon in push_subscribers:
                    locations.add((round(lat, 1), round(lon, 1)))

                for lat_r, lon_r in locations:
                    loc_key = f"{lat_r},{lon_r}"
                    alert_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat_r}&lon={lon_r}&exclude=minutely,hourly,daily&appid={OPENWEATHER_API_KEY}"
                    try:
                        res = requests.get(alert_url, timeout=5)
                        if res.ok:
                            active_alerts_cache[loc_key] = res.json().get('alerts', [])
                    except Exception as e:
                        print(f"Failed to fetch alerts for {loc_key}: {e}")

                # Notify Email Subscribers
                for email, lat, lon, prefs_json in email_subscribers:
                    loc_key = f"{round(lat, 1)},{round(lon, 1)}"
                    alerts = active_alerts_cache.get(loc_key, [])
                    if not alerts: continue
                    
                    prefs = json.loads(prefs_json) if prefs_json else {"types": ["severe", "rain", "temp", "air"]}
                    for alert in alerts:
                        if utils.is_alert_relevant(alert, prefs):
                            advice = utils.get_ai_advice(alert)
                            utils.send_alert_email(email, alert, advice)

                # Notify Push Subscribers
                for endpoint, p256dh, auth, lat, lon in push_subscribers:
                    loc_key = f"{round(lat, 1)},{round(lon, 1)}"
                    alerts = active_alerts_cache.get(loc_key, [])
                    if not alerts: continue

                    for alert in alerts:
                        if alert.get('event'):
                            push_data = json.dumps({
                                "title": f"⚠️ {alert['event']}",
                                "body": alert.get('description', 'Severe weather alert in your area.'),
                                "url": "/weather"
                            })
                            subscription_info = {
                                "endpoint": endpoint,
                                "keys": {"p256dh": p256dh, "auth": auth}
                            }
                            send_push_notification(subscription_info, push_data, VAPID_PRIVATE_KEY, VAPID_CLAIMS)

                time.sleep(3600)  # Check every hour
            except Exception as e:
                print(f"Weather alert background task error: {e}")
                time.sleep(60)

def trigger_daily_forecast_webhooks(app_context):
    """Background task to trigger daily forecast webhooks."""
    with app_context:
        OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
        
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
                                if (datetime.utcnow().replace(tzinfo=timezone.utc) - last).total_seconds() > 72000: # 20 hours
                                    should_send = True
                            except:
                                should_send = True
                        
                        if should_send:
                            weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={sub['lat']}&lon={sub['lon']}&units=metric&appid={OPENWEATHER_API_KEY}"
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
                        print(f"Error processing subscription {sub['id']}: {sub_e}")
                        continue

                time.sleep(300) # Check every 5 minutes
            except Exception as e:
                print(f"Daily forecast webhook task error: {e}")
                time.sleep(60)
