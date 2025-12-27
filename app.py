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
from contextlib import contextmanager


def check_weather_alerts():
    """Background task to check for severe weather alerts for all subscribers."""
    with app.app_context():
        while True:
            try:
                with get_db() as conn:
                    cursor = conn.cursor()
                    # Left join to get preferences
                    cursor.execute("""
                        SELECT s.email, s.lat, s.lon, up.alert_thresholds 
                        FROM subscriptions s 
                        LEFT JOIN user_preferences up ON s.email = up.email 
                        WHERE s.lat IS NOT NULL
                    """)
                    subscribers = cursor.fetchall()
                
                # Cache alerts by location to avoid rate limits (simple rounding)
                active_alerts_cache = {} # Key: "lat,lon" (rounded), Value: list of alerts

                for email, lat, lon, prefs_json in subscribers:
                    # Parse Prefs
                    prefs = {"types": ["severe", "rain", "temp", "air"], "severity": "medium"} # Default all
                    if prefs_json:
                        try:
                             loaded = json.loads(prefs_json)
                             if isinstance(loaded, dict):
                                 prefs = loaded
                        except:
                            pass
                    
                    # Round lat/lon to 1 decimal place (~11km) for caching
                    loc_key = f"{round(lat, 1)},{round(lon, 1)}"
                    
                    alerts = []
                    if loc_key in active_alerts_cache:
                        alerts = active_alerts_cache[loc_key]
                    else:
                        # Fetch from OWM
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
                        
                        # FILTERING LOGIC
                        user_types = prefs.get("types", [])
                        is_relevant = False
                        
                        # Mapping
                        keyword_map = {
                            "severe": ["tornado", "hurricane", "thunderstorm", "warning", "danger", "severe"],
                            "rain": ["rain", "flood", "shower", "storm"],
                            "temp": ["heat", "cold", "freeze", "frost", "advisory"],
                            "air": ["air quality", "pollution", "smoke", "fire"]
                        }
                        
                        # If user selected NO types, send nothing (unless default logic applies)
                        if not user_types:
                             continue

                        for t in user_types:
                            keywords = keyword_map.get(t, [])
                            if any(k in event_lower for k in keywords) or any(k in desc_lower for k in keywords):
                                is_relevant = True
                                break
                        
                        if not is_relevant:
                            continue

                        # Use Gemini for advice
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

                        # Send via Resend (Email)
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


                
                time.sleep(3600)  # Check every hour
            except Exception as e:
                app.logger.error(f"Weather alert background task error: {e}")
                time.sleep(60)

def trigger_daily_forecast_webhooks():
    """Background task to trigger daily forecast webhooks."""
    with app.app_context():
        while True:
            try:
                # Check for daily forecasts that haven't been sent in the last 20 hours
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
                            
                        # Check if triggered recently
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
                                should_send = True # Fallback if date parsing fails
                        
                        if should_send:
                            # Fetch forecast
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
                            
                            # Update last_triggered
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

                time.sleep(300) # Check every 5 minutes
                
            except Exception as e:
                app.logger.error(f"Daily forecast webhook task error: {e}")
                time.sleep(60)




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
        # If 410 Gone, we should delete the subscription (not implemented here for brevity)
        return False
    except Exception as e:
        app.logger.error(f"Push Error: {e}")
        return False
from dotenv import load_dotenv
from jinja2.exceptions import TemplateSyntaxError
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_seasurf import SeaSurf
import utils
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join('assets', 'user_uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


load_dotenv()

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="assets",
    static_url_path="/assets",
)

# Security Configuration
app.secret_key = os.environ.get("FLASK_SECRET_KEY")
if not app.secret_key:
    if os.environ.get("VERCEL"):
        raise ValueError("FLASK_SECRET_KEY must be set in production!")
    app.secret_key = "synocast-dev-secret-change-me"

# Session Security
app.config.update(
    SESSION_COOKIE_SECURE=True if os.environ.get("VERCEL") else False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
)

# Initialize Security Extensions
csrf = SeaSurf(app)
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["1000 per day", "200 per hour"],
    storage_uri="memory://",
)

# Content Security Policy configuration
csp = {
    'default-src': [
        '\'self\'',
        'https://cdn.jsdelivr.net',
        'https://cdnjs.cloudflare.com',
    ],
    'style-src': [
        '\'self\'',
        '\'unsafe-inline\'',
        'https://cdn.jsdelivr.net',
        'https://fonts.googleapis.com',
        'https://cdnjs.cloudflare.com',
        'https://unpkg.com',
    ],
    'font-src': [
        '\'self\'',
        'https://fonts.gstatic.com',
        'https://cdnjs.cloudflare.com',
    ],
    'script-src': [
        '\'self\'',
        '\'unsafe-inline\'',
        'https://cdn.jsdelivr.net',
        'https://unpkg.com',
    ],
    'img-src': [
        '\'self\'',
        'data:',
        'https://*', # Allow images from any secure source for news/weather
    ],
}

talisman = Talisman(
    app,
    content_security_policy=csp,
    force_https=True if os.environ.get("VERCEL") else False
)

WEATHER_CACHE = {}
CACHE_DURATION = 600

if os.environ.get("VERCEL"):
    DATABASE = "/tmp/subscriptions.db"
else:
    DATABASE = os.path.join(app.root_path, "subscriptions.db")

# API Keys
resend.api_key = os.environ.get("RESEND_API_KEY")
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

# VAPID Keys
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY")
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY")
VAPID_CLAIMS = {
    "sub": f"mailto:{os.environ.get('REPLY_TO_EMAIL', 'admin@synocast.app')}"
}

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Create the subscriptions and preferences tables if they do not already exist."""
    with get_db() as conn:
        try:
            # Subscriptions table with location support
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    phone TEXT,
                    lat REAL,
                    lon REAL,
                    subscription_type TEXT DEFAULT 'email',
                    created_at TEXT NOT NULL
                )
                """
            )
            
            # Weather reports for community verification
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS weather_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lat REAL,
                    lon REAL,
                    city TEXT,
                    reported_condition TEXT,
                    api_condition TEXT,
                    reported_at TEXT,
                    is_accurate INTEGER
                )
                """
            )
            
            # User preferences for alerts and global settings
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE,
                    alert_thresholds TEXT, -- JSON string
                    notification_channels TEXT, -- JSON string
                    phone_number TEXT,
                    language TEXT DEFAULT 'en',
                    timezone TEXT,
                    currency TEXT DEFAULT 'USD'
                )
                """
            )
            
            # Push Subscriptions
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS push_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint TEXT UNIQUE,
                    p256dh TEXT,
                    auth TEXT,
                    lat REAL,
                    lon REAL,
                    created_at TEXT
                )
                """
            )
            
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(subscriptions)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if "phone" not in columns:
                conn.execute("ALTER TABLE subscriptions ADD COLUMN phone TEXT")
            if "subscription_type" not in columns:
                conn.execute("ALTER TABLE subscriptions ADD COLUMN subscription_type TEXT DEFAULT 'email'")
            if "lat" not in columns:
                conn.execute("ALTER TABLE subscriptions ADD COLUMN lat REAL")
            if "lon" not in columns:
                conn.execute("ALTER TABLE subscriptions ADD COLUMN lon REAL")
                
            conn.commit()

            # Check weather_reports columns
            cursor.execute("PRAGMA table_info(weather_reports)")
            wr_columns = [column[1] for column in cursor.fetchall()]
            if "comment" not in wr_columns:
                conn.execute("ALTER TABLE weather_reports ADD COLUMN comment TEXT")
            if "email" not in wr_columns:
                conn.execute("ALTER TABLE weather_reports ADD COLUMN email TEXT")

            # Weather Photos Table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS weather_photos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    lat REAL,
                    lon REAL,
                    city TEXT,
                    caption TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            
            # Favorite Locations Table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS favorite_locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    lat REAL,
                    lon REAL,
                    city TEXT,
                    country TEXT,
                    created_at TEXT
                )
                """
            )

            # Check user_preferences columns
            cursor.execute("PRAGMA table_info(user_preferences)")
            up_columns = [column[1] for column in cursor.fetchall()]
            
            if "temperature_unit" not in up_columns:
                conn.execute("ALTER TABLE user_preferences ADD COLUMN temperature_unit TEXT DEFAULT 'C'")
            if "activities" not in up_columns:
                conn.execute("ALTER TABLE user_preferences ADD COLUMN activities TEXT")
            if "dashboard_config" not in up_columns:
                conn.execute("ALTER TABLE user_preferences ADD COLUMN dashboard_config TEXT")
            if "health_config" not in up_columns:
                conn.execute("ALTER TABLE user_preferences ADD COLUMN health_config TEXT")
            if "language" not in up_columns:
                conn.execute("ALTER TABLE user_preferences ADD COLUMN language TEXT DEFAULT 'en'")
            if "timezone" not in up_columns:
                conn.execute("ALTER TABLE user_preferences ADD COLUMN timezone TEXT")
            if "currency" not in up_columns:
                conn.execute("ALTER TABLE user_preferences ADD COLUMN currency TEXT DEFAULT 'USD'")

            # Weather Idioms Table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS weather_idioms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    condition TEXT NOT NULL,
                    idiom TEXT NOT NULL,
                    language TEXT NOT NULL,
                    meaning TEXT,
                    cultural_context TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )

            # Currency Rates Table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS currency_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    base_currency TEXT NOT NULL,
                    target_currency TEXT NOT NULL,
                    rate REAL NOT NULL,
                    last_updated TEXT NOT NULL
                )
                """
            )

            # Gamification Tables
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    points INTEGER DEFAULT 0,
                    event_type TEXT,
                    description TEXT,
                    created_at TEXT
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS badges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    description TEXT,
                    icon_class TEXT,
                    threshold INTEGER
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_badges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    badge_id INTEGER,
                    awarded_at TEXT,
                    UNIQUE(email, badge_id)
                )
                """
            )
            
            # Pre-seed basic badges if empty
            cursor.execute("SELECT COUNT(*) FROM badges")
            if cursor.fetchone()[0] == 0:
                badges_data = [
                    ("Novice Reporter", "Submit your first weather report", "fa-seedling", 1),
                    ("Reliable Source", "Submit 5 accurate weather reports", "fa-check-double", 5),
                    ("Storm Chaser", "Report severe weather accurately", "fa-bolt", 0), # Special condition
                    ("Community Pillar", "Reach 500 karma points", "fa-crown", 500)
                ]
                cursor.executemany("INSERT INTO badges (name, description, icon_class, threshold) VALUES (?, ?, ?, ?)", badges_data)



            
            # Historical Weather Cache Table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS historical_weather_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lat REAL NOT NULL,
                    lon REAL NOT NULL,
                    date TEXT NOT NULL,
                    temp_max REAL,
                    temp_min REAL,
                    temp_mean REAL,
                    precipitation REAL,
                    wind_speed REAL,
                    weather_code INTEGER,
                    source TEXT,
                    cached_at TEXT NOT NULL,
                    UNIQUE(lat, lon, date)
                )
                """
            )
            
            # Create index for faster historical queries
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_historical_location_date 
                ON historical_weather_cache(lat, lon, date)
                """
            )
            
            # Climate Records Table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS climate_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lat REAL NOT NULL,
                    lon REAL NOT NULL,
                    record_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    date TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(lat, lon, record_type)
                )
                """
            )
            
            # Create index for faster record queries
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_records_location 
                ON climate_records(lat, lon, record_type)
                """
            )

            conn.commit()
            
            # Ensure upload directory exists (skip on Vercel - read-only filesystem)
            if not os.environ.get("VERCEL"):
                try:
                    if not os.path.exists(UPLOAD_FOLDER):
                        os.makedirs(UPLOAD_FOLDER)
                except Exception as dir_error:
                    app.logger.warning(f"Could not create upload folder: {dir_error}")

                
        except Exception as e:
            app.logger.error(f"Database initialization error: {e}")

# Initialize the DB at import time
try:
    init_db()
except Exception as e:
    app.logger.error(f"Database initialization failed: {e}")

@app.route('/sw.js')
def service_worker():
    from flask import send_from_directory
    return send_from_directory('.', 'sw.js', mimetype='application/javascript')

@app.route('/robots.txt')
def robots_txt():
    from flask import send_from_directory
    return send_from_directory('.', 'robots.txt')

@app.route('/sitemap.xml')
def sitemap_xml():
    from flask import send_from_directory
    return send_from_directory('.', 'sitemap.xml')

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('logo/logo-small.svg')

@app.route('/health')
def health_check():
    """Health check endpoint for debugging deployment issues."""
    import sys
    return jsonify({
        "status": "ok",
        "python_version": sys.version,
        "environment": "vercel" if os.environ.get("VERCEL") else "local",
        "env_vars_set": {
            "FLASK_SECRET_KEY": bool(os.environ.get("FLASK_SECRET_KEY")),
            "OPENWEATHER_API_KEY": bool(os.environ.get("OPENWEATHER_API_KEY")),
            "RESEND_API_KEY": bool(os.environ.get("RESEND_API_KEY")),
            "GEMINI_API_KEY": bool(os.environ.get("GEMINI_API_KEY")),
            "NEWS_API_KEY": bool(os.environ.get("NEWS_API_KEY")),
            "VAPID_PRIVATE_KEY": bool(os.environ.get("VAPID_PRIVATE_KEY")),
            "VAPID_PUBLIC_KEY": bool(os.environ.get("VAPID_PUBLIC_KEY"))
        }
    })

@app.route("/")
def home():
    dt_info = utils.get_local_time_string()
    gemini_key = os.environ.get("GEMINI_API_KEY")
    news_key = os.environ.get("NEWS_API_KEY")
    
    # Robust local query: only include city/country if known
    location_parts = []
    if dt_info.get('city') and dt_info.get('city').lower() != "unknown":
        location_parts.append(dt_info.get('city'))
    if dt_info.get('country') and dt_info.get('country').lower() != "unknown":
        location_parts.append(dt_info.get('country'))
    
    local_query = f"weather {' '.join(location_parts)}" if location_parts else "weather extreme events"
    
    seo_meta = {
        "description": "SynoCast provides AI-enhanced weather storytelling, hyper-local forecasts, and curated weather news using Gemini AI.",
        "keywords": "weather, AI weather, weather news, local forecast, SynoCast, climate events, severe weather alerts"
    }
    
    # Latest Headlines
    raw_latest = utils.fetch_weather_news(query=local_query, page_size=15, api_key=news_key)
    # If local news empty, try general weather news
    if not raw_latest:
        raw_latest = utils.fetch_weather_news(query="weather breaking", page_size=10, api_key=news_key)
        
    latest_news = utils.categorize_news_with_ai(raw_latest, gemini_key)
    
    # Around The World news
    raw_world = utils.fetch_weather_news(query="global weather major events", page_size=10, api_key=news_key)
    world_news = utils.categorize_news_with_ai(raw_world, gemini_key)
    
    return render_template(
        "home.html", 
        active_page="home", 
        date_time_info=dt_info,
        latest_news=latest_news,
        world_news=world_news,
        meta=seo_meta
    )


@app.route("/news")
def news():
    dt_info = utils.get_local_time_string()
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    seo_meta = {
        "description": "Stay updated with SynoCast's AI-curated weather headlines, breaking alerts, and featured climate stories from around the globe.",
        "keywords": "breaking news, weather alerts, climate change stories, storm warnings, weather news today"
    }
    
    # Fetch a larger pool of news to categorize and filter
    raw_news = utils.fetch_weather_news(query="extreme weather climate impact", page_size=20, api_key=NEWS_API_KEY)
    all_categorized = utils.categorize_news_with_ai(raw_news, gemini_key)
    
    # Breaking News: High/Critical urgency
    breaking_news = [a for a in all_categorized if a.get('urgency') in ['Critical', 'High']]
    
    # Featured Stories: Climate Events, Weather Impact News, Hydrological Updates
    featured_news = [a for a in all_categorized if a.get('category') in ['Climate Events', 'Weather Impact News', 'Hydrological Updates']]
    
    # Fallback if filters are too strict
    if not breaking_news:
        breaking_news = all_categorized[:4]
    if not featured_news:
        featured_news = all_categorized[4:8]

    return render_template(
        "news.html", 
        active_page="news", 
        date_time_info=dt_info,
        breaking_news=breaking_news,
        featured_news=featured_news,
        meta=seo_meta
    )


@app.route("/weather")
def weather():
    dt_info = utils.get_local_time_string()
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    seo_meta = {
        "description": "Get detailed local weather forecasts, interactive maps, and AI-driven weather insights with SynoCast.",
        "keywords": "local weather, hourly forecast, weather map, AI weather recommendations, humidity, wind speed"
    }
    
    # Weather News Section: Categorized by relevance
    raw_weather = utils.fetch_weather_news(query="local weather forecast updates", country=dt_info.get('country'), page_size=10, api_key=NEWS_API_KEY)
    weather_news = utils.categorize_news_with_ai(raw_weather, gemini_key)
    
    return render_template(
        "weather.html", 
        active_page="weather", 
        date_time_info=dt_info,
        weather_news=weather_news,
        meta=seo_meta
    )


@app.route("/subscribe")
def subscribe():
    seo_meta = {
        "description": "Subscribe to SynoCast for hyper-local weather alerts and daily AI weather news delivered directly to your inbox.",
        "keywords": "subscribe, weather alerts, email notifications, SynoCast subscription"
    }
    return render_template("subscribe.html", active_page="subscribe", date_time_info=utils.get_local_time_string(), meta=seo_meta)


@app.route("/about")
def about():
    seo_meta = {
        "description": "Learn more about SynoCast, our mission to provide AI-enhanced weather storytelling, and how we use technology to keep you ahead of the storm.",
        "keywords": "about SynoCast, weather company, AI weather technology, mission"
    }
    return render_template("about.html", active_page="about", date_time_info=utils.get_local_time_string(), meta=seo_meta)


@app.route("/offline")
def offline():
    """Offline fallback page."""
    return render_template("offline.html", active_page="offline", date_time_info=utils.get_local_time_string())

@app.route("/profile")
def profile():
    """User Profile Page."""
    if 'user_email' not in session:
        # If not logged in, redirect to home or show a message? 
        # For now, let's just render it but the template will show "Please log in".
        # Or better, redirect to home with a query param to open modal.
        return render_template("profile.html", active_page="profile", date_time_info=utils.get_local_time_string(), user=None)
    
    email = session['user_email']
    user_data = {}
    
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get Subscription Info
        c.execute("SELECT * FROM subscriptions WHERE email = ?", (email,))
        sub = c.fetchone()
        if sub:
            user_data['subscription'] = dict(sub)
            
        # Get Preferences
        c.execute("SELECT * FROM user_preferences WHERE email = ?", (email,))
        prefs = c.fetchone()
        if prefs:
            user_data['preferences'] = dict(prefs)
            # Parse JSON fields if they exist as strings (though database is TEXT)
            try:
                 if user_data['preferences'].get('activities'):
                     user_data['preferences']['activities'] = json.loads(user_data['preferences']['activities'])
            except:
                 user_data['preferences']['activities'] = []
                 
            try:
                 if user_data['preferences'].get('dashboard_config'):
                     user_data['preferences']['dashboard_config'] = json.loads(user_data['preferences']['dashboard_config'])
            except:
                 user_data['preferences']['dashboard_config'] = {}
        else:
             # Default dummy prefs
             user_data['preferences'] = {"temperature_unit": "C", "activities": [], "dashboard_config": {}}

        # Get Favorites
        c.execute("SELECT * FROM favorite_locations WHERE email = ? ORDER BY created_at DESC", (email,))
        favs = [dict(row) for row in c.fetchall()]
    return render_template("profile.html", active_page="profile", date_time_info=utils.get_local_time_string(), user=user_data)




@app.route("/api/user/logout", methods=["POST"])
def logout():
    session.pop('user_email', None)
    return jsonify({"success": True})

@app.route("/api/user/profile", methods=["GET", "POST"])
def api_user_profile():
    if 'user_email' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    email = session['user_email']
    
    if request.method == "GET":
        # Return simplified JSON logic if needed, but the HTML route handles the main view
        pass

    if request.method == "POST":
        data = request.json
        temp_unit = data.get("temperature_unit")
        activities = data.get("activities") # List
        dashboard_config = data.get("dashboard_config") # Dict
        language = data.get("language", "en")
        timezone_pref = data.get("timezone")
        currency = data.get("currency", "USD")
        
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM user_preferences WHERE email = ?", (email,))
                exists = cursor.fetchone()
                
                if exists:
                    conn.execute("""
                        UPDATE user_preferences 
                        SET temperature_unit = ?, activities = ?, dashboard_config = ?, 
                            language = ?, timezone = ?, currency = ?
                        WHERE email = ?
                    """, (temp_unit, json.dumps(activities), json.dumps(dashboard_config), 
                          language, timezone_pref, currency, email))
                else:
                    conn.execute("""
                        INSERT INTO user_preferences (email, temperature_unit, activities, dashboard_config, language, timezone, currency)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (email, temp_unit, json.dumps(activities), json.dumps(dashboard_config), 
                          language, timezone_pref, currency))
                
                conn.commit()
            return jsonify({"success": True})
        except Exception as e:
            app.logger.error(f"Profile update error: {e}")
            return jsonify({"error": str(e)}), 500

@app.route("/api/user/favorites", methods=["GET", "POST", "DELETE"])
def api_user_favorites():
    if 'user_email' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    email = session['user_email']
    
    if request.method == "GET":
        with get_db() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM favorite_locations WHERE email = ? ORDER BY created_at DESC", (email,))
            rows = [dict(r) for r in c.fetchall()]
        return jsonify(rows)

    if request.method == "POST":
        data = request.json
        lat = data.get('lat')
        lon = data.get('lon')
        city = data.get('city')
        country = data.get('country')
        
        if not lat or not lon:
            return jsonify({"error": "Missing coordinates"}), 400
            
        with get_db() as conn:
            # Check duplicates
            c = conn.cursor()
            c.execute("SELECT id FROM favorite_locations WHERE email = ? AND lat = ? AND lon = ?", (email, lat, lon))
            if c.fetchone():
                return jsonify({"success": True, "message": "Already a favorite"})
                
            conn.execute(
                "INSERT INTO favorite_locations (email, lat, lon, city, country, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (email, lat, lon, city, country, datetime.utcnow().isoformat())
            )
            conn.commit()
        return jsonify({"success": True})

    if request.method == "DELETE":
        fav_id = request.args.get('id')
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        with get_db() as conn:
            if fav_id:
                conn.execute("DELETE FROM favorite_locations WHERE id = ? AND email = ?", (fav_id, email))
            elif lat and lon:
                conn.execute("DELETE FROM favorite_locations WHERE lat = ? AND lon = ? AND email = ?", (lat, lon, email))
            conn.commit()
        return jsonify({"success": True})

@app.route("/api/update-session-location", methods=["POST"])
def update_session_location():
    """Update server-side session with client-granted location info."""
    data = request.get_json(silent=True) or {}
    city = data.get("city")
    region = data.get("region")
    utc_offset = data.get("utc_offset")
    
    if city and utc_offset:
        # Check current IP to handle potential IP changes (though unlikely within session)
        ip = utils.get_client_ip()
        session["location_data"] = {
            "ip": ip,
            "city": city,
            "region": region,
            "utc_offset": utc_offset
        }
        return jsonify({"success": True})
    
    return jsonify({"success": False, "error": "Missing data"}), 400

@app.route("/api/ip-location")
def api_ip_location():
    """Get approximate location based on user's public IP."""
    try:
        # Check common IP headers from proxies/CDNs
        user_ip = request.headers.get('CF-Connecting-IP') or \
                  request.headers.get('X-Real-IP') or \
                  request.headers.get('X-Forwarded-For', request.remote_addr)
        
        if user_ip and ',' in user_ip:
            user_ip = user_ip.split(',')[0].strip()

        # If we're on localhost, the API might fail for 127.0.0.1
        # But for the deployed site, it will have a real public IP
        url = f"http://ip-api.com/json/{user_ip}?fields=status,lat,lon,city,countryCode"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        data = res.json()
        
        # If the local IP fails, as a last resort, try calling without IP to let the API use the server's breakout IP (less accurate but valid)
        if data.get('status') == 'fail' and user_ip in ['127.0.0.1', '::1']:
            res = requests.get("http://ip-api.com/json/?fields=status,lat,lon,city,countryCode", timeout=5)
            data = res.json()

        return jsonify(data)
    except Exception as e:
        app.logger.error(f"IP Location error: {e}")
        return jsonify({"status": "fail", "message": str(e)}), 500

@app.route("/api/weather")
@limiter.limit("30 per minute")
def api_weather():
    """
    Proxy endpoint for OpenWeatherMap API.
    Required params: lat, lon
    """
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if not lat or not lon:
        return jsonify({"error": "Missing lat or lon parameters"}), 400

    # Check Cache
    cache_key = f"{lat},{lon}"
    now_ts = datetime.utcnow().timestamp()
    
    if cache_key in WEATHER_CACHE:
        cached_entry = WEATHER_CACHE[cache_key]
        if now_ts - cached_entry["timestamp"] < CACHE_DURATION:
            app.logger.info(f"Serving weather for {cache_key} from cache")
            return jsonify(cached_entry["data"])

    try:
        current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
        pollution_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"

        # Using more workers for better concurrency
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_current = executor.submit(requests.get, current_url, timeout=5)
            future_forecast = executor.submit(requests.get, forecast_url, timeout=5)
            future_pollution = executor.submit(requests.get, pollution_url, timeout=5)

            current_res = future_current.result()
            forecast_res = future_forecast.result()
            pollution_res = future_pollution.result()

        current_res.raise_for_status()
        forecast_res.raise_for_status()
        pollution_res.raise_for_status()

        current_data = current_res.json()
        forecast_data = forecast_res.json()
        pollution_data = pollution_res.json()

        result = {
            "current": current_data,
            "forecast": forecast_data,
            "pollution": pollution_data
        }

        # Update Cache
        WEATHER_CACHE[cache_key] = {
            "timestamp": now_ts,
            "data": result
        }

        return jsonify(result)

    except Exception as e:
        app.logger.error(f"OpenWeatherMap API error: {e}")
        return jsonify({"error": "Failed to fetch weather data"}), 500


@app.route("/api/widget-data")
@limiter.limit("60 per minute")
def api_widget_data():
    """
    Compact weather data endpoint optimized for widgets and push notifications.
    Returns minimal data for display in notifications, periodic sync, and offline storage.
    """
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if not lat or not lon:
        return jsonify({"error": "Missing lat or lon parameters"}), 400

    try:
        # Fetch current weather only (lightweight request)
        current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
        current_res = requests.get(current_url, timeout=5)
        current_res.raise_for_status()
        current_data = current_res.json()

        # Extract only essential data for widget/notification display
        widget_data = {
            "location": {
                "city": current_data.get("name", "Unknown"),
                "country": current_data.get("sys", {}).get("country", ""),
                "lat": lat,
                "lon": lon
            },
            "current": {
                "temp": round(current_data["main"]["temp"], 1),
                "feels_like": round(current_data["main"]["feels_like"], 1),
                "temp_min": round(current_data["main"]["temp_min"], 1),
                "temp_max": round(current_data["main"]["temp_max"], 1),
                "humidity": current_data["main"]["humidity"],
                "pressure": current_data["main"]["pressure"],
                "weather": {
                    "main": current_data["weather"][0]["main"],
                    "description": current_data["weather"][0]["description"],
                    "icon": current_data["weather"][0]["icon"]
                },
                "wind_speed": round(current_data["wind"]["speed"], 1),
                "clouds": current_data.get("clouds", {}).get("all", 0)
            },
            "timestamp": int(datetime.utcnow().timestamp()),
            "sunrise": current_data.get("sys", {}).get("sunrise"),
            "sunset": current_data.get("sys", {}).get("sunset")
        }

        # Add rain/snow data if available
        if "rain" in current_data:
            widget_data["current"]["rain_1h"] = current_data["rain"].get("1h", 0)
        if "snow" in current_data:
            widget_data["current"]["snow_1h"] = current_data["snow"].get("1h", 0)

        return jsonify(widget_data)

    except Exception as e:
        app.logger.error(f"Widget data API error: {e}")
        return jsonify({"error": "Failed to fetch widget data"}), 500


@app.route("/api/weather/analytics")
def api_weather_analytics():
    """
    Returns aggregated daily forecast data for analytics charts.
    """
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if not lat or not lon:
        return jsonify({"error": "Missing lat or lon parameters"}), 400

    # reusing same cache key and duration
    cache_key = f"{lat},{lon}"
    now_ts = datetime.utcnow().timestamp()
    
    weather_data = None

    # Check Cache
    if cache_key in WEATHER_CACHE:
        cached_entry = WEATHER_CACHE[cache_key]
        if now_ts - cached_entry["timestamp"] < CACHE_DURATION:
            weather_data = cached_entry["data"]

    # If not in cache, we need to fetch it (same logic as api_weather)
    # Ideally we'd redirect or call api_weather, but for now we'll just return error 
    # if it's not cached because the frontend usually calls api_weather first.
    # But to be robust, let's just re-fetch if needed.
    if not weather_data:
        try:
            # Simplified synchronous fetch if not cached (analytics is secondary)
            forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
            res = requests.get(forecast_url, timeout=5)
            res.raise_for_status()
            forecast_data = res.json()
            # We also need city timezone from forecast data
            weather_data = {"forecast": forecast_data}
            # We don't update the global cache here to avoid partial updates, 
            # or we could if we fetched everything. Let's just use what we have.
        except Exception as e:
            app.logger.error(f"Analytics fetch error: {e}")
            return jsonify({"error": "Failed to fetch weather data"}), 500

    try:
        forecast = weather_data["forecast"]
        timezone_offset = forecast["city"]["timezone"]
        analytics = utils.aggregate_forecast_data(forecast["list"], timezone_offset)
        return jsonify(analytics)
    except KeyError as e:
        app.logger.error(f"Analytics data parse error: {e}")
        return jsonify({"error": "Invalid weather data format"}), 500


@app.route("/api/weather/health")
@limiter.limit("20 per minute")
def api_weather_health():
    """
    Returns AI-generated health insights based on current weather.
    Cached for 1 hour to save API credits.
    """
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    
    if not lat or not lon:
        return jsonify({"error": "Missing coordinates"}), 400
        
    cache_key = f"health_{round(float(lat), 1)}_{round(float(lon), 1)}"
    now_ts = datetime.utcnow().timestamp()
    
    if cache_key in WEATHER_CACHE:
        entry = WEATHER_CACHE[cache_key]
        if now_ts - entry['timestamp'] < 3600: # 1 hour cache
            return jsonify(entry['data'])

    try:
        # 1. Fetch current weather (fast)
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
        w_res = requests.get(url, timeout=5)
        if not w_res.ok:
            return jsonify({"error": "Weather data unavailable"}), 502
        w_data = w_res.json()
        
        # 2. Get AI Analysis
        # Construct lean prompt
        weather_summary = (
            f"Temp: {w_data['main']['temp']}C, Humidity: {w_data['main']['humidity']}%, "
            f"Pressure: {w_data['main']['pressure']}hPa, Window: {w_data['wind']['speed']}m/s, "
            f"Condition: {w_data['weather'][0]['description']}"
        )
        
        prompt = f"""
        Analyze this weather for health impacts: "{weather_summary}".
        Return ONLY valid JSON (no markdown) with this structure:
        {{
            "migraine": {{"risk": "Low/Medium/High", "reason": "short explanation"}},
            "arthritis": {{"risk": "Low/Medium/High", "reason": "short explanation"}},
            "respiratory": {{"risk": "Low/Medium/High", "reason": "short explanation"}},
            "uv_skin": {{"risk": "Low/Medium/High", "reason": "short explanation"}},
            "general_advice": "One sentence summary."
        }}
        """
        
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
             # Fallback if no AI key
             return jsonify({
                 "migraine": {"risk": "Unknown", "reason": "AI unavailable"},
                 "general_advice": "Stay safe!"
             })

        client = genai.Client(api_key=gemini_key.strip())
        
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            analysis = json.loads(response.text)
        except Exception as e:
            app.logger.warning(f"Gemini 2.0 error: {e}. Trying fallback.")
            try:
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=prompt,
                    config={'response_mime_type': 'application/json'}
                )
                analysis = json.loads(response.text)
            except Exception as e2:
                 app.logger.error(f"All Gemini models failed: {e2}")
                 return jsonify({
                     "migraine": {"risk": "Unknown", "reason": "Service busy"},
                     "arthritis": {"risk": "Unknown", "reason": "Service busy"},
                     "respiratory": {"risk": "Unknown", "reason": "Service busy"},
                     "uv_skin": {"risk": "Unknown", "reason": "Service busy"},
                     "general_advice": "Health insights currently unavailable due to high demand. Please try again later."
                 })
        
        # Cache it
        WEATHER_CACHE[cache_key] = {
            "timestamp": now_ts,
            "data": analysis
        }
        
        return jsonify(analysis)

    except Exception as e:
        app.logger.error(f"Health API error: {e}")
        return jsonify({"error": "Health analysis failed"}), 500


@app.route("/api/weather/extended")
@limiter.limit("30 per minute")
def api_weather_extended():
    """
    Fetches extended forecast data using One Call API 3.0.
    Returns:
    - 8-day daily forecast with astronomy data
    - 48-hour hourly forecast
    - Sunrise/sunset with golden hours for photographers
    - Moon phase calendar
    """
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if not lat or not lon:
        return jsonify({"error": "Missing lat or lon parameters"}), 400

    # Extended forecast cache (separate from regular weather cache)
    cache_key = f"extended_{lat},{lon}"
    now_ts = datetime.utcnow().timestamp()
    
    # Check cache (10 minute duration for extended forecast)
    EXTENDED_CACHE_DURATION = 600
    if cache_key in WEATHER_CACHE:
        cached_entry = WEATHER_CACHE[cache_key]
        if now_ts - cached_entry["timestamp"] < EXTENDED_CACHE_DURATION:
            app.logger.info(f"Serving extended forecast for {lat},{lon} from cache")
            return jsonify(cached_entry["data"])

    try:
        # One Call API 3.0 endpoint
        # Note: This requires a subscription. Free tier provides 1,000 calls/day
        onecall_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
        
        res = requests.get(onecall_url, timeout=10)
        
        # If One Call API 3.0 fails (e.g., not subscribed), fall back to free tier simulation
        if res.status_code == 401 or res.status_code == 403:
            app.logger.warning("One Call API 3.0 not available. Falling back to free tier simulation.")
            return simulate_extended_forecast(lat, lon)
        
        res.raise_for_status()
        data = res.json()
        
        # Extract timezone offset
        timezone_offset = data.get('timezone_offset', 0)
        
        # Process daily forecast (8 days)
        daily_forecast = []
        for day in data.get('daily', [])[:8]:
            day_data = {
                "dt": day.get('dt'),
                "date": datetime.fromtimestamp(day['dt'], tz=timezone.utc).strftime('%a, %b %d'),
                "temp": {
                    "min": round(day['temp']['min'], 1),
                    "max": round(day['temp']['max'], 1),
                    "day": round(day['temp'].get('day', day['temp']['max']), 1)
                },
                "weather": {
                    "main": day['weather'][0]['main'],
                    "description": day['weather'][0]['description'],
                    "icon": day['weather'][0]['icon']
                },
                "humidity": day.get('humidity'),
                "wind_speed": round(day.get('wind_speed', 0), 1),
                "pop": round(day.get('pop', 0) * 100),  # Probability of precipitation
                "uvi": round(day.get('uvi', 0), 1),
                "clouds": day.get('clouds', 0)
            }
            
            # Add astronomy data
            astronomy = utils.format_astronomy_data(day, timezone_offset)
            if astronomy:
                day_data["astronomy"] = astronomy
            
            daily_forecast.append(day_data)
        
        # Process hourly forecast (48 hours)
        hourly_forecast = []
        for hour in data.get('hourly', [])[:48]:
            hour_data = {
                "dt": hour.get('dt'),
                "time": datetime.fromtimestamp(hour['dt'], tz=timezone.utc).strftime('%H:%M'),
                "date": datetime.fromtimestamp(hour['dt'], tz=timezone.utc).strftime('%a %d'),
                "temp": round(hour['temp'], 1),
                "feels_like": round(hour.get('feels_like', hour['temp']), 1),
                "weather": {
                    "main": hour['weather'][0]['main'],
                    "description": hour['weather'][0]['description'],
                    "icon": hour['weather'][0]['icon']
                },
                "humidity": hour.get('humidity'),
                "wind_speed": round(hour.get('wind_speed', 0), 1),
                "pop": round(hour.get('pop', 0) * 100),
                "clouds": hour.get('clouds', 0)
            }
            hourly_forecast.append(hour_data)
        
        result = {
            "daily": daily_forecast,
            "hourly": hourly_forecast,
            "timezone_offset": timezone_offset
        }
        
        # Update cache
        WEATHER_CACHE[cache_key] = {
            "timestamp": now_ts,
            "data": result
        }
        
        return jsonify(result)
    
    except Exception as e:
        app.logger.error(f"Extended forecast API error: {e}")
        # Try fallback simulation
        try:
            return simulate_extended_forecast(lat, lon)
        except:
            return jsonify({"error": "Failed to fetch extended forecast data"}), 500


def simulate_extended_forecast(lat, lon):
    """
    Simulate extended forecast using free tier 5-day forecast API.
    This is a fallback when One Call API 3.0 is not available.
    """
    try:
        # Fetch 5-day forecast from free tier
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
        res = requests.get(forecast_url, timeout=5)
        res.raise_for_status()
        forecast_data = res.json()
        
        timezone_offset = forecast_data['city']['timezone']
        forecast_list = forecast_data['list']
        
        # Aggregate into daily forecasts
        daily_data = {}
        for item in forecast_list:
            dt_utc = datetime.fromtimestamp(item['dt'], tz=timezone.utc)
            dt_local = dt_utc + timedelta(seconds=timezone_offset)
            date_str = dt_local.strftime('%Y-%m-%d')
            
            if date_str not in daily_data:
                daily_data[date_str] = {
                    'temps': [],
                    'conditions': [],
                    'humidity': [],
                    'wind': [],
                    'pop': [],
                    'dt': item['dt']
                }
            
            daily_data[date_str]['temps'].append(item['main']['temp'])
            daily_data[date_str]['conditions'].append(item['weather'][0])
            daily_data[date_str]['humidity'].append(item['main']['humidity'])
            daily_data[date_str]['wind'].append(item['wind']['speed'])
            daily_data[date_str]['pop'].append(item.get('pop', 0))
        
        # Create daily forecast (5 days from API + 3 simulated)
        daily_forecast = []
        sorted_dates = sorted(daily_data.keys())[:5]
        
        for date_str in sorted_dates:
            day = daily_data[date_str]
            dt_obj = datetime.fromtimestamp(day['dt'], tz=timezone.utc) + timedelta(seconds=timezone_offset)
            
            daily_forecast.append({
                "dt": day['dt'],
                "date": dt_obj.strftime('%a, %b %d'),
                "temp": {
                    "min": round(min(day['temps']), 1),
                    "max": round(max(day['temps']), 1),
                    "day": round(sum(day['temps']) / len(day['temps']), 1)
                },
                "weather": {
                    "main": day['conditions'][0]['main'],
                    "description": day['conditions'][0]['description'],
                    "icon": day['conditions'][0]['icon']
                },
                "humidity": round(sum(day['humidity']) / len(day['humidity'])),
                "wind_speed": round(sum(day['wind']) / len(day['wind']), 1),
                "pop": round(max(day['pop']) * 100),
                "simulated": False
            })
        
        # Simulate 3 additional days (simple extrapolation)
        if daily_forecast:
            last_day = daily_forecast[-1]
            for i in range(1, 4):
                future_dt = datetime.fromtimestamp(last_day['dt'], tz=timezone.utc) + timedelta(days=i)
                daily_forecast.append({
                    "dt": int(future_dt.timestamp()),
                    "date": future_dt.strftime('%a, %b %d'),
                    "temp": last_day['temp'],  # Reuse last known temps
                    "weather": last_day['weather'],
                    "humidity": last_day['humidity'],
                    "wind_speed": last_day['wind_speed'],
                    "pop": last_day['pop'],
                    "simulated": True
                })
        
        # Create hourly forecast from available data (up to 40 hours from free tier)
        hourly_forecast = []
        for item in forecast_list[:16]:  # ~48 hours
            dt_utc = datetime.fromtimestamp(item['dt'], tz=timezone.utc)
            dt_local = dt_utc + timedelta(seconds=timezone_offset)
            
            hourly_forecast.append({
                "dt": item['dt'],
                "time": dt_local.strftime('%H:%M'),
                "date": dt_local.strftime('%a %d'),
                "temp": round(item['main']['temp'], 1),
                "feels_like": round(item['main']['feels_like'], 1),
                "weather": {
                    "main": item['weather'][0]['main'],
                    "description": item['weather'][0]['description'],
                    "icon": item['weather'][0]['icon']
                },
                "humidity": item['main']['humidity'],
                "wind_speed": round(item['wind']['speed'], 1),
                "pop": round(item.get('pop', 0) * 100),
                "clouds": item.get('clouds', {}).get('all', 0)
            })
        
        # Add simulated astronomy data to each day
        # Since free tier doesn't provide this, we'll calculate approximate values
        import math
        from datetime import date
        
        for day_forecast in daily_forecast:
            dt_obj = datetime.fromtimestamp(day_forecast['dt'], tz=timezone.utc) + timedelta(seconds=timezone_offset)
            
            # Approximate sunrise/sunset based on latitude (simplified calculation)
            # This is a rough approximation - real calculation would use astronomical algorithms
            try:
                # Get lat from the API call (we have it from the request)
                # For simulation, use generic times adjusted by timezone
                base_sunrise_hour = 6  # 6 AM baseline
                base_sunset_hour = 18  # 6 PM baseline
                
                # Simulate sunrise/sunset times (simplified)
                sunrise_time = dt_obj.replace(hour=base_sunrise_hour, minute=30, second=0, microsecond=0)
                sunset_time = dt_obj.replace(hour=base_sunset_hour, minute=30, second=0, microsecond=0)
                
                # Calculate moon phase (simplified lunar cycle approximation)
                # Lunar cycle is approximately 29.53 days
                # Use a known new moon date and calculate from there
                known_new_moon = datetime(2024, 1, 11, tzinfo=timezone.utc)  # Known new moon
                days_since = (dt_obj.replace(tzinfo=timezone.utc) - known_new_moon).days
                lunar_cycle = 29.53
                moon_phase_value = (days_since % lunar_cycle) / lunar_cycle
                
                # Format astronomy data
                astronomy_data = {
                    "sunrise": sunrise_time.strftime("%H:%M"),
                    "sunset": sunset_time.strftime("%H:%M"),
                    "moonrise": (sunrise_time + timedelta(hours=1)).strftime("%H:%M"),
                    "moonset": (sunset_time - timedelta(hours=1)).strftime("%H:%M"),
                    "moon_phase": utils.interpret_moon_phase(moon_phase_value),
                    "sunrise_ts": int(sunrise_time.timestamp()),
                    "sunset_ts": int(sunset_time.timestamp())
                }
                
                # Calculate golden hours
                golden_hours = utils.calculate_golden_hours(
                    int(sunrise_time.timestamp()),
                    int(sunset_time.timestamp()),
                    timezone_offset
                )
                if golden_hours:
                    astronomy_data["golden_hours"] = golden_hours
                
                day_forecast["astronomy"] = astronomy_data
            except Exception as e:
                app.logger.warning(f"Failed to calculate astronomy data: {e}")
                # Skip astronomy data for this day if calculation fails
                pass
        
        result = {
            "daily": daily_forecast,
            "hourly": hourly_forecast,
            "timezone_offset": timezone_offset,
            "note": "Extended forecast simulated from 5-day free tier API. Upgrade to One Call API 3.0 for full features."
        }
        
        return jsonify(result)
    
    except Exception as e:
        app.logger.error(f"Simulated extended forecast error: {e}")
        raise



@app.route("/api/weather/history")
def api_weather_history():
    """
    Proxy endpoint for historical weather data.
    Since OWM History API often requires a subscription, we'll provide 
    a mix of current forecast trends and some randomized historical noise for demo purposes.
    """
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if not lat or not lon:
        return jsonify({"error": "Missing lat or lon parameters"}), 400

    try:
        # For a truly functional historical view in a free tier, 
        # we often use the 'forecast' data which gives 5 days / 3 hour steps.
        # We'll extract representative daily points from it.
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
        res = requests.get(forecast_url, timeout=5)
        res.raise_for_status()
        data = res.json()

        # Process data into a simpler historical-like trend
        # We'll take the first point of each day in the forecast
        history = []
        seen_days = set()
        
        for item in data.get('list', []):
            dt = datetime.fromtimestamp(item['dt'], tz=timezone.utc)
            day_str = dt.strftime('%Y-%m-%d')
            if day_str not in seen_days:
                history.append({
                    "date": dt.strftime('%b %d'),
                    "temp": round(item['main']['temp']),
                    "condition": item['weather'][0]['main'],
                    "humidity": item['main']['humidity'],
                    "wind": item['wind']['speed']
                })
                seen_days.add(day_str)
            if len(history) >= 5:
                break

        # If we have less than 5 days, just return what we have
        return jsonify(history)

    except Exception as e:
        app.logger.error(f"History API error: {e}")
        # Robust fallback for demo - generate 5 days of random-ish data based on a base temp
        base_temp = 25
        demo_history = []
        for i in range(5):
            date = (datetime.now() - timedelta(days=5-i)).strftime('%b %d')
            demo_history.append({
                "date": date,
                "temp": base_temp + random.randint(-5, 5),
                "condition": random.choice(["Clear", "Clouds", "Rain"]),
                "humidity": random.randint(40, 80),
                "wind": round(random.uniform(2, 8), 1)
            })
        return jsonify(demo_history)


@app.route("/api/geocode/search")
@limiter.limit("20 per minute")
def geocode_search():
    """Proxy endpoint for Nominatim forward geocoding (search)."""
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    
    try:
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={query}"
        headers = {'User-Agent': 'SynoCast/1.0', 'Accept-Language': 'en'}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        app.logger.error(f"Geocode search error: {e}")
        return jsonify({"error": "Failed to fetch location data"}), 500


@app.route("/api/proxy/tiles/<layer>/<z>/<x>/<y>")
@limiter.limit("200 per minute")
def proxy_tiles(layer, z, x, y):
    """
    Proxy OWM tiles to hide API key.
    URL format: /api/proxy/tiles/{layer}/{z}/{x}/{y}
    Example layer: clouds_new, precipitation_new, pressure_new, wind_new, temp_new
    """
    allowed_layers = ["clouds_new", "precipitation_new", "pressure_new", "wind_new", "temp_new"]
    if layer not in allowed_layers:
        return "Invalid layer", 400

    # Ensure .png extension is handled
    if not y.lower().endswith(".png"):
        y = f"{y}.png"

    tile_url = f"https://tile.openweathermap.org/map/{layer}/{z}/{x}/{y}?appid={OPENWEATHER_API_KEY}"
    
    try:
        # Stream the response to avoid loading large images into memory
        req = requests.get(tile_url, stream=True, timeout=5)
        if req.status_code == 200:
            return req.content, 200, {'Content-Type': 'image/png'}
        else:
            return "Tile not found", req.status_code
    except Exception as e:
        app.logger.error(f"Tile proxy error: {e}")
        return "Proxy error", 500


@app.route("/api/geocode/reverse")
@limiter.limit("60 per minute")
def geocode_reverse():
    """Proxy endpoint for Nominatim reverse geocoding."""
    lat = request.args.get('lat', '')
    lon = request.args.get('lon', '')
    
    if not lat or not lon:
        return jsonify({"error": "Parameters 'lat' and 'lon' are required"}), 400
    
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
        headers = {'User-Agent': 'SynoCast/1.0', 'Accept-Language': 'en'}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        app.logger.error(f"Reverse geocode error: {e}")
        return jsonify({"error": "Failed to fetch location data"}), 500


@app.route("/otp", methods=["POST"])
@limiter.limit("5 per minute; 20 per day")
def otp():
    try:
        action = request.form.get("action")
        sub_type = request.form.get("type", "email") # Default to email
        
        if action == "request":
            contact_info = None
            if sub_type == "email":
                contact_info = request.form.get("email")
                if not contact_info:
                    return jsonify({"success": False, "message": "Please enter your email address."}), 400
            else:
                return jsonify({"success": False, "message": "Invalid subscription type."}), 400

            # Check if already subscribed (for subscription flow) OR if user exists (for login flow)
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM subscriptions WHERE email = ?", (contact_info,))
                exists = cursor.fetchone()

            # For strictly "requesting subscription", arguably we should error if exists.
            # But now we want to support "Login" via the same flow.
            # So we will proceed to send OTP in BOTH cases.
            
            # Generate OTP
            otp_code = "".join([str(random.randint(0, 9)) for _ in range(6)])
            print(f"\n[DEBUG] Generated OTP for {contact_info}: {otp_code}\n")
            session["expected_otp"] = otp_code
            session["pending_contact"] = contact_info
            session["pending_type"] = sub_type
            session["pending_preferences"] = request.form.get("preferences")
            # We track if it's a new sub or login
            session["is_new_subscription"] = not bool(exists)

            # Send OTP (Email)
            subject_line = "SynoCast Login OTP" if exists else "Your SynoCast Subscription OTP"
            intro_text = "Welcome back!" if exists else "Thank you for subscribing to SynoCast."

            # Send OTP (Email)
            try:
                # Using onboarding@resend.dev as the sender to ensure delivery without domain verification.
                # The user's email is set as Reply-To.
                r = resend.Emails.send({
                    "from": "SynoCast <onboarding@resend.dev>", 
                    "to": contact_info,
                    "reply_to": os.environ.get("REPLY_TO_EMAIL", "afnanulhaq4@gmail.com"),
                    "subject": subject_line,
                    "html": f"""
                    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                        <h2 style="color: #333;">Welcome to SynoCast!</h2>
                        <p>{intro_text} Please use the following One-Time Password (OTP) to complete your request:</p>
                        <p style="font-size: 24px; font-weight: bold; text-align: center; color: #007bff;">{otp_code}</p>
                        <p>This OTP is valid for a short period. Do not share it with anyone.</p>
                        <p>If you did not request this, please ignore this email.</p>
                        <p>Best regards,<br>The SynoCast Team</p>
                    </div>
                    """
                })
                app.logger.info(f"OTP email sent to {contact_info}. Resend ID: {r['id']}")
                return jsonify({"success": True, "step": "otp", "email": contact_info})
            except Exception as e:
                error_msg = str(e)
                # Handle Resend testing restriction
                if "testing emails" in error_msg:
                    print(f"\\n[DEV MODE] Resend Restriction: OTP for {contact_info} is {otp_code}\\n")
                    return jsonify({"success": True, "step": "otp", "email": contact_info, "message": "Test mode: OTP logged to console."})
                
                app.logger.error(f"Failed to send OTP email: {e}")
                return jsonify({"success": False, "message": "Failed to send OTP. Please try again later."}), 500

        elif action == "verify":
            submitted_otp = request.form.get("otp")
            contact_info = session.get("pending_contact")
            sub_type = session.get("pending_type", "email")
            expected_otp = session.get("expected_otp")
            
            if not contact_info or not expected_otp:
                return jsonify({"success": False, "message": "Session expired. Please start again."}), 400

            if submitted_otp == expected_otp:
                pending_prefs = session.get("pending_preferences")
                is_new = session.get("is_new_subscription", True)

                # Clear Auth Session Params
                session.pop("pending_contact", None)
                session.pop("expected_otp", None)
                session.pop("pending_type", None)
                session.pop("pending_preferences", None)
                session.pop("is_new_subscription", None)
                
                with get_db() as conn:
                    if is_new:
                        conn.execute(
                            "INSERT INTO subscriptions (email, subscription_type, created_at) VALUES (?, ?, ?)",
                            (contact_info, sub_type, datetime.utcnow().isoformat()),
                        )
                    
                    if pending_prefs:
                        # Save preferences if provided
                        conn.execute(
                            """
                            INSERT OR REPLACE INTO user_preferences 
                            (email, alert_thresholds, notification_channels) 
                            VALUES (?, ?, ?)
                            """,
                            (contact_info, pending_prefs, json.dumps(["email"]))
                        )
                    conn.commit()
                
                # Set Session for Login
                session['user_email'] = contact_info

                return jsonify({"success": True, "step": "success", "is_login": not session.get("is_new_subscription", True)})

            return jsonify({"success": False, "message": "Incorrect OTP. Please try again."}), 400

        return jsonify({"success": False, "message": "Invalid action."}), 400
    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return jsonify({"success": False, "message": "An internal server error occurred."}), 500


@app.route("/api/push/vapid-public-key")
def get_vapid_public_key():
    return jsonify({"publicKey": VAPID_PUBLIC_KEY})

@app.route("/api/push/subscribe", methods=["POST"])
def push_subscribe():
    data = request.get_json(silent=True) or {}
    subscription = data.get("subscription")
    location = data.get("location", {})
    
    if not subscription or not subscription.get("endpoint"):
        return jsonify({"error": "Invalid subscription"}), 400

    try:
        with get_db() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO push_subscriptions 
                (endpoint, p256dh, auth, lat, lon, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    subscription["endpoint"],
                    subscription["keys"]["p256dh"],
                    subscription["keys"]["auth"],
                    location.get("lat"),
                    location.get("lon"),
                    datetime.utcnow().isoformat()
                )
            )
            conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        app.logger.error(f"Push subscribe error: {e}")
        return jsonify({"error": "Database error"}), 500


@app.route("/api/ai_chat", methods=["POST"])
@limiter.limit("5 per minute; 50 per day")
def api_ai_chat():
    """
    Chat endpoint that uses Google Gemini with weather context.
    Expects JSON: { "message": "user question", "lat": float, "lon": float }
    """
    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "")
    lat = data.get("lat")
    lon = data.get("lon")

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    # Initialize weather context variables
    weather_context = ""
    temp, cond, city = None, None, None
    
    # If lat/lon not in request, try to get them via IP
    if not (lat and lon):
        try:
            ip = utils.get_client_ip()
            if ip.startswith("127.") or ip == "localhost" or ip == "::1":
                # Default to Islamabad for local development
                lat, lon = 33.6844, 73.0479
            else:
                resp_ip = requests.get(f"https://ipapi.co/{ip}/json/", timeout=2)
                if resp_ip.ok:
                    ip_data = resp_ip.json()
                    lat, lon = ip_data.get("latitude"), ip_data.get("longitude")
                    app.logger.info(f"IP-based location detection: {lat}, {lon}")
        except Exception as e:
            app.logger.warning(f"IP-based location fallback failed: {e}")

    if lat and lon:
        try:
            # Fetch current weather for context
            current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
            resp = requests.get(current_url, timeout=5)
            resp.raise_for_status()
            w_data = resp.json()
            
            temp = w_data['main']['temp']
            cond = w_data['weather'][0]['description']
            humidity = w_data['main']['humidity']
            wind = w_data['wind']['speed']
            city = w_data.get('name', 'your location')
            
            weather_context = (
                f"\n\nCURRENT WEATHER CONTEXT for {city}:\n"
                f"- Temperature: {temp}°C\n"
                f"- Conditions: {cond}\n"
                f"- Humidity: {humidity}%\n"
                f"- Wind Speed: {wind} m/s\n"
                "CRITICAL: Use this data to answer. DO NOT ask the user for their location if this context is present."
            )
        except Exception as e:
            app.logger.warning(f"Could not fetch weather context for AI: {e}")

    system_prompt = (
        "You are SynoBot, a powerful AI weather assistant for the SynoCast website. "
        "Your goal is to provide immediate, context-aware answers. "
        "You can discuss current weather, long-term forecasts, daily life impacts (traffic, air quality, pollen), "
        "personal outfit suggestions, and weather-based recipe ideas. "
        "If CURRENT WEATHER CONTEXT is provided below, use it to answer directly. "
        "NEVER ask for the user's city, zip code, or location if the context is already provided. "
        "Examples: "
        "- For 'Should I carry an umbrella?', mention the rain and city name. "
        "- For 'What should I wear?', give clothing advice based on temperature. "
        "- For 'What's for dinner?', suggest a recipe fitting the current conditions. "
        "Keep responses friendly, concise, and helpful."
    )

    # Use environment variable for Gemini API key
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    
    if not gemini_api_key:
         # Demo mode fallback instead of 500 error
         demo_reply = (
             "Hi! I'm SynoBot. Currently, I'm running in **Demo Mode** because a Gemini API Key hasn't been configured yet. "
             "Once you add your key to the .env file and restart the server, I'll be able to give you deep AI insights! "
         )
         if city and temp:
             demo_reply += f"\n\nIn the meantime, I can see it's currently {temp}°C with {cond} in {city}!"
         return jsonify({"reply": demo_reply})

    try:
        # Strip the key to ensure no whitespace/newlines cause issues
        gemini_api_key = gemini_api_key.strip()
        genai.configure(api_key=gemini_api_key)
        # Using the latest balanced model alias to avoid versioning 404s
        model = genai.GenerativeModel("gemini-flash-latest")
        
        full_prompt = f"{system_prompt}{weather_context}\n\nUser: {user_message}"


        
        response = model.generate_content(full_prompt)
        
        if response and response.text:
             return jsonify({"reply": response.text})
        else:
             return jsonify({"reply": "I'm sorry, I couldn't generate a response. Please try again."})

    except Exception as e:
        app.logger.error(f"Gemini API error: {e}")
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg:
            return jsonify({"reply": "It looks like the Gemini API Key is invalid. Please check your .env file."})
        return jsonify({"reply": "I'm experiencing some technical difficulties. My AI engine is taking a break!"})

# ============================================================================
# AI Enhancements - New Endpoints
# ============================================================================

@app.route("/api/weather/impacts")
@limiter.limit("20 per minute")
def api_weather_impacts():
    """
    Returns weather impact predictions for traffic, air quality, and pollen.
    Query params: lat, lon
    """
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    
    if not lat or not lon:
        return jsonify({"error": "Missing lat/lon parameters"}), 400
    
    try:
        # Fetch current weather data
        current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
        resp = requests.get(current_url, timeout=5)
        resp.raise_for_status()
        w_data = resp.json()
        
        # Get air quality data
        aqi_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
        aqi_resp = requests.get(aqi_url, timeout=5)
        current_aqi = None
        if aqi_resp.ok:
            aqi_data = aqi_resp.json()
            if aqi_data.get('list'):
                # OWM API index is 1-5. 1=Good, 5=Very Poor.
                # We'll map this roughly to the AQI scale (0-500) for our logic
                current_aqi = aqi_data['list'][0]['main']['aqi'] * 50 
        
        # Extract weather parameters
        temperature = w_data['main']['temp']
        humidity = w_data['main']['humidity']
        wind_speed = w_data['wind']['speed']
        weather_condition = w_data['weather'][0]
        
        # Calculate all impacts
        impacts = utils.get_all_impacts(
            weather_condition,
            temperature,
            humidity,
            wind_speed,
            current_aqi
        )
        
        return jsonify(impacts)
        
    except Exception as e:
        app.logger.error(f"Weather impacts error: {e}")
        return jsonify({"error": "Failed to calculate weather impacts"}), 500


@app.route("/api/ai/outfit", methods=["POST"])
@limiter.limit("10 per minute")
def api_ai_outfit():
    """
    Returns personalized outfit suggestions with AI descriptions.
    Payload: { "lat": float, "lon": float, "activity": string }
    """
    data = request.get_json(silent=True) or {}
    lat = data.get("lat")
    lon = data.get("lon")
    activity = data.get("activity", "casual")
    
    if not lat or not lon:
        return jsonify({"error": "Missing lat/lon parameters"}), 400
    
    try:
        # Fetch current weather data
        current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
        resp = requests.get(current_url, timeout=5)
        resp.raise_for_status()
        w_data = resp.json()
        
        # Get forecast for precipitation probability
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
        forecast_resp = requests.get(forecast_url, timeout=5)
        precip_prob = 0
        if forecast_resp.ok:
            f_data = forecast_resp.json()
            if f_data.get('list'):
                # Use current precipitation probability (pop)
                precip_prob = f_data['list'][0].get('pop', 0) * 100
        
        # Extract weather parameters
        temperature = w_data['main']['temp']
        condition = w_data['weather'][0]['main']
        wind_speed = w_data['wind']['speed']
        
        # Get outfit suggestion
        outfit = utils.get_outfit_suggestion(
            temperature,
            condition,
            precip_prob,
            activity,
            wind_speed
        )
        
        return jsonify({
            "outfit": outfit,
            "weather": {
                "temperature": temperature,
                "condition": condition,
                "city": w_data.get('name', 'your location')
            }
        })
        
    except Exception as e:
        app.logger.error(f"Outfit suggestion error: {e}")
        return jsonify({"error": "Failed to generate outfit suggestion"}), 500


@app.route("/api/weather/recipes")
@limiter.limit("20 per minute")
def api_weather_recipes():
    """
    Returns weather-based recipe suggestions.
    Query params: lat, lon, meal_type (optional)
    """
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    meal_type = request.args.get("meal_type")
    
    if not lat or not lon:
        return jsonify({"error": "Missing lat/lon parameters"}), 400
    
    try:
        # Fetch current weather data
        current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
        resp = requests.get(current_url, timeout=5)
        resp.raise_for_status()
        w_data = resp.json()
        
        # Extract weather parameters
        temperature = w_data['main']['temp']
        condition = w_data['weather'][0]['main']
        
        # Get recipe suggestions
        recipes = utils.get_recipe_suggestions(
            temperature,
            condition,
            meal_type,
            count=3
        )
        
        # Format recipes for frontend
        formatted_recipes = [utils.format_recipe_for_display(r) for r in recipes]
        
        return jsonify({
            "recipes": formatted_recipes,
            "weather": {
                "temperature": temperature,
                "condition": condition,
                "city": w_data.get('name', 'your location')
            }
        })
        
    except Exception as e:
        app.logger.error(f"Recipe suggestions error: {e}")
        return jsonify({"error": "Failed to get recipe suggestions"}), 500



@app.route("/api/recommendations", methods=["POST"])
@limiter.limit("5 per minute; 50 per day")
def api_recommendations():
    """Provides AI-driven clothing and activity recommendations based on weather."""
    data = request.get_json(silent=True) or {}
    lat = data.get("lat")
    lon = data.get("lon")
    
    if not lat or not lon:
        return jsonify({"error": "Location required"}), 400
        
    try:
        current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
        resp = requests.get(current_url, timeout=5)
        resp.raise_for_status()
        w = resp.json()
        
        prompt = (
            f"Given these weather conditions in {w.get('name')}: {w['main']['temp']}°C, {w['weather'][0]['description']}, "
            f"humidity {w['main']['humidity']}%, wind {w['wind']['speed']}m/s. "
            "Suggest appropriate clothing and 1-2 outdoor activities. Keep it concise (max 3 sentences)."
        )
        
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_api_key:
            return jsonify({"recommendation": "Wear comfortable layers and stay prepared for the day!"})
            
        genai.configure(api_key=gemini_api_key.strip())
        model = genai.GenerativeModel("gemini-flash-latest")
        response = model.generate_content(prompt)
        
        return jsonify({"recommendation": response.text if response.text else "Enjoy your day!"})
    except Exception as e:
        app.logger.error(f"Recommendations error: {e}")
        return jsonify({"recommendation": "Stay safe and check local updates."})

@app.route("/api/trip_plan")
@limiter.limit("5 per minute")
def api_trip_plan():
    """AI Weather Trip Planner with Gemini."""
    destination = request.args.get("destination")
    dates = request.args.get("dates") # e.g., "Dec 28 - Jan 5"
    purpose = request.args.get("purpose", "general travel")

    if not destination or not dates:
        return jsonify({"error": "Destination and dates are required"}), 400

    try:
        # 1. Geocode destination
        geo_url = f"https://nominatim.openstreetmap.org/search?format=json&q={destination}&limit=1"
        headers = {'User-Agent': 'SynoCast/1.0'}
        geo_res = requests.get(geo_url, headers=headers, timeout=5)
        if not geo_res.ok or not geo_res.json():
             return jsonify({"error": "Could not find location"}), 404
        
        loc = geo_res.json()[0]
        lat, lon = loc['lat'], loc['lon']

        # 2. Get forecast/climatology context
        # For trip planning, usually 5-day forecast is enough if trip is soon, 
        # otherwise we'd need climatology. We'll fetch current & forecast as proxy.
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
        resp = requests.get(forecast_url, timeout=5)
        forecast_context = ""
        if resp.ok:
            f_data = resp.json()
            # Summarize forecast for AI
            summary = []
            for i in range(0, min(len(f_data.get('list', [])), 40), 8): # Every 24h
                try:
                    day = f_data['list'][i]
                    temp = day.get('main', {}).get('temp', 'N/A')
                    desc = day.get('weather', [{}])[0].get('description', 'N/A')
                    date_str = datetime.fromtimestamp(day['dt']).strftime('%b %d')
                    summary.append(f"{date_str}: {temp}°C, {desc}")
                except Exception as e:
                    app.logger.warning(f"Error parsing forecast day {i}: {e}")
            forecast_context = "\n".join(summary)

        # 3. Ask Gemini for advice
        prompt = (
            f"Plan a trip to {destination} for {dates}. Purpose: {purpose}.\n"
            f"Weather Context (Next 5 days):\n{forecast_context}\n\n"
            "Provide:\n1. Detailed packing suggestions (clothing, gear).\n"
            "2. Travel recommendations based on expected weather.\n"
            "3. One specific 'SynoTip' for this trip.\n"
            "Keep it engaging and helpful."
        )

        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_api_key:
            return jsonify({"plan": "Gemini API key missing. Please configure it to see your AI trip plan!"})

        genai.configure(api_key=gemini_api_key.strip())
        model = genai.GenerativeModel("gemini-flash-latest")
        response = model.generate_content(prompt)

        return jsonify({"plan": response.text})
    except Exception as e:
        app.logger.error(f"Trip Planner error: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to generate trip plan: {str(e)}"}), 500

@app.route("/api/weather/compare")
def api_weather_compare():
    """Weather Duel Comparison Tool."""
    city1 = request.args.get("city1")
    city2 = request.args.get("city2")

    if not city1 or not city2:
        return jsonify({"error": "Two cities are required"}), 400

    def get_weather(city):
        geo_url = f"https://nominatim.openstreetmap.org/search?format=json&q={city}&limit=1"
        headers = {'User-Agent': 'SynoCast/1.0'}
        geo_res = requests.get(geo_url, headers=headers, timeout=5)
        if not geo_res.ok or not geo_res.json(): return None
        loc = geo_res.json()[0]
        w_url = f"https://api.openweathermap.org/data/2.5/weather?lat={loc['lat']}&lon={loc['lon']}&units=metric&appid={OPENWEATHER_API_KEY}"
        w_res = requests.get(w_url, timeout=5)
        return w_res.json() if w_res.ok else None

    with concurrent.futures.ThreadPoolExecutor() as executor:
        f1 = executor.submit(get_weather, city1)
        f2 = executor.submit(get_weather, city2)
        w1, w2 = f1.result(), f2.result()

    if not w1 or not w2:
        return jsonify({"error": "Failed to fetch weather for one or both cities"}), 404

    return jsonify({"city1": w1, "city2": w2})

@app.route("/api/weather/historical")
@limiter.limit("20 per minute")
def api_weather_historical():
    """
    Enhanced Historical Weather Insights: On This Day.
    Fetches data from cache or Open-Meteo, calculates climate anomalies.
    """
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    years_ago = int(request.args.get('years', 5))

    if not lat or not lon:
        return jsonify({"error": "lat and lon required"}), 400

    try:
        # Calculate target date
        target_date = datetime.now() - timedelta(days=365 * years_ago)
        date_str = target_date.strftime('%Y-%m-%d')
        
        historical_data = None
        
        # 1. Check database cache
        with get_db() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM historical_weather_cache WHERE lat = ? AND lon = ? AND date = ?", 
                (round(float(lat), 4), round(float(lon), 4), date_str)
            )
            row = cursor.fetchone()
            if row:
                historical_data = dict(row)
                app.logger.info(f"Serving historical data for {date_str} from DB cache")

        # 2. If not in cache, fetch from API
        if not historical_data:
            historical_data = utils.fetch_historical_weather(lat, lon, date_str)
            if historical_data:
                # Save to DB cache
                try:
                    with get_db() as conn:
                        conn.execute(
                            """
                            INSERT OR REPLACE INTO historical_weather_cache 
                            (lat, lon, date, temp_max, temp_min, temp_mean, precipitation, wind_speed, weather_code, source, cached_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                round(float(lat), 4), round(float(lon), 4), date_str,
                                historical_data['temp_max'], historical_data['temp_min'], 
                                historical_data['temp_mean'], historical_data['precipitation'],
                                historical_data['wind_speed'], historical_data['weather_code'],
                                historical_data['source'], datetime.utcnow().isoformat()
                            )
                        )
                        conn.commit()
                except Exception as db_err:
                    app.logger.error(f"Failed to cache historical data: {db_err}")

        if not historical_data:
            return jsonify({"error": "Failed to fetch historical data"}), 500

        # 3. Fetch Climate Normals (30-year average) for this month
        month = target_date.month
        normals = utils.fetch_climate_normals(float(lat), float(lon), month)
        
        # 4. Calculate Anomaly
        anomaly = None
        if normals and historical_data.get('temp_mean') is not None:
            anomaly = utils.calculate_climate_anomaly(historical_data['temp_mean'], normals['temp_mean_avg'])

        return jsonify({
            "status": "success",
            "years_ago": years_ago,
            "date": date_str,
            "data": historical_data,
            "climatology": normals,
            "anomaly": anomaly
        })

    except Exception as e:
        app.logger.error(f"Historical API error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/weather/climate-trends")
@limiter.limit("10 per minute")
def api_weather_climate_trends():
    """
    Returns seasonal patterns and trends for a location.
    """
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    years = int(request.args.get('years', 5))

    if not lat or not lon:
        return jsonify({"error": "lat and lon required"}), 400

    try:
        trends = utils.analyze_seasonal_trends(float(lat), float(lon), years_back=years)
        if not trends:
            return jsonify({"error": "Failed to analyze climate trends"}), 500
            
        return jsonify(trends)
    except Exception as e:
        app.logger.error(f"Climate trends API error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/weather/records")
@limiter.limit("10 per minute")
def api_weather_records():
    """
    Returns record-breaking temperatures for a location.
    Checks cache first, then fetches from historical archive.
    """
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if not lat or not lon:
        return jsonify({"error": "lat and lon required"}), 400

    try:
        # Check database for records first
        records = {}
        with get_db() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM climate_records WHERE lat = ? AND lon = ?", 
                (round(float(lat), 4), round(float(lon), 4))
            )
            rows = cursor.fetchall()
            for row in rows:
                records[row['record_type']] = {
                    "value": row['value'],
                    "date": row['date'],
                    "year": row['year']
                }

        # If no records or data is stale (older than 30 days), fetch from API
        if not records:
            api_records = utils.get_record_temperatures(float(lat), float(lon), years_back=10)
            if api_records:
                # Save to DB
                try:
                    with get_db() as conn:
                        for r_type in ['record_high', 'record_low']:
                            data = api_records[r_type]
                            conn.execute(
                                """
                                INSERT OR REPLACE INTO climate_records 
                                (lat, lon, record_type, value, date, year, updated_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    round(float(lat), 4), round(float(lon), 4), r_type,
                                    data['temperature'], data['date'], data['year'],
                                    datetime.utcnow().isoformat()
                                )
                            )
                        conn.commit()
                except Exception as db_err:
                    app.logger.error(f"Failed to cache climate records: {db_err}")
                
                records = api_records

        return jsonify(records)
    except Exception as e:
        app.logger.error(f"Climate records API error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/report_weather", methods=["POST"])
def api_report_weather():
    """Community Verification System."""
    data = request.json
    lat = data.get('lat')
    lon = data.get('lon')
    city = data.get('city')
    reported_condition = data.get('condition')
    comment = data.get('comment', '')
    api_condition = data.get('api_condition')
    is_accurate = 1 if reported_condition.lower() == api_condition.lower() else 0

    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO weather_reports (lat, lon, city, reported_condition, comment, api_condition, reported_at, is_accurate) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (lat, lon, city, reported_condition, comment, api_condition, datetime.utcnow().isoformat(), is_accurate)
            )
            conn.commit()
        return jsonify({"success": True, "message": "Report submitted. Thanks for verifying!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/community")
def community():
    seo_meta = {
        "description": "Join the SynoCast community. Share weather photos, report local conditions, and plan your outdoor activities with AI.",
        "keywords": "weather community, photos, weather reports, event planner, outdoor activities"
    }
    return render_template("community.html", active_page="community", date_time_info=utils.get_local_time_string(), meta=seo_meta)

@app.route("/api/community/photo", methods=["POST"])
def api_upload_photo():
    if 'photo' not in request.files:
         return jsonify({"error": "No file part"}), 400
    file = request.files['photo']
    if file.filename == '':
         return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Unique filename to prevent overwrites (timestamp prefix)
        unique_name = f"{int(datetime.utcnow().timestamp())}_{filename}"
        filepath = os.path.join(app.root_path, UPLOAD_FOLDER, unique_name)
        file.save(filepath)
        
        # Save to DB
        lat = request.form.get('lat')
        lon = request.form.get('lon')
        city = request.form.get('city')
        caption = request.form.get('caption')
        
        with get_db() as conn:
            conn.execute(
                "INSERT INTO weather_photos (filename, lat, lon, city, caption, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (unique_name, lat, lon, city, caption, datetime.utcnow().isoformat())
            )
            conn.commit()
            
        return jsonify({"success": True})
    
    return jsonify({"error": "Invalid file type"}), 400

@app.route("/api/community/feed")
def api_community_feed():
    limit = request.args.get('limit', 20)
    try:
        with get_db() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # Photos
            c.execute("SELECT *, 'photo' as type FROM weather_photos ORDER BY created_at DESC LIMIT ?", (limit,))
            photos = [dict(row) for row in c.fetchall()]
            
            # Reports
            c.execute("SELECT *, 'report' as type FROM weather_reports ORDER BY reported_at DESC LIMIT ?", (limit,))
            reports = [dict(row) for row in c.fetchall()]
            
        # Combine and sort
        feed = photos + reports
        # Helper to get date safely
        def get_date(x):
            return x.get('created_at') or x.get('reported_at')
            
        feed.sort(key=lambda x: get_date(x), reverse=True)
        return jsonify(feed[:int(limit)])
    except Exception as e:
        app.logger.error(f"Feed error: {e}")
        return jsonify([])

@app.route("/api/planning/suggest", methods=["POST"])
@limiter.limit("10 per minute")
def api_planning_suggest():
    data = request.json
    activity = data.get("activity")
    lat = data.get("lat")
    lon = data.get("lon")
    
    if not activity or not lat:
         return jsonify({"error": "Activity and location required"}), 400
         
    # Get Forecast
    forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
    try:
        res = requests.get(forecast_url, timeout=5)
        res.raise_for_status()
        forecast = res.json()
        
        # Prepare context for AI
        # We'll valid next 5 days
        days_ctx = []
        for i in range(0, min(len(forecast['list']), 40), 8):
            day = forecast['list'][i]
            dt_txt = day['dt_txt']
            temp = day['main']['temp']
            weather = day['weather'][0]['description']
            days_ctx.append(f"{dt_txt}: {temp}C, {weather}")
            
        context = "\n".join(days_ctx)
        
        prompt = (
            f"I want to do '{activity}'. Based on this forecast:\n{context}\n"
            "Suggest the best day(s) and time(s) for this activity. "
            "Give brief reasons. Format as simple HTML (e.g. <ul><li>...</li></ul>)."
        )
        
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
             return jsonify({"html": "<p>Configure Gemini API for suggestions.</p>"})
             
        client = genai.Client(api_key=gemini_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt
        )
        
        return jsonify({"html": response.text})
        
    except Exception as e:
        app.logger.error(f"Planning error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/currency/rates")
def api_currency_rates():
    """
    Returns latest currency exchange rates.
    In a real app, this would fetch from a service like Fixer.io or OpenExchangeRates.
    Here we provide live-like rates for major currencies.
    """
    # Check DB cache first
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT target_currency, rate FROM currency_rates WHERE base_currency = 'USD'")
            rows = cursor.fetchall()
            
            rates = {row[0]: row[1] for row in rows}
            
            # If DB is empty, use defaults and populate
            if not rates:
                default_rates = {
                    "USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 150.25, 
                    "CNY": 7.21, "PKR": 278.5, "INR": 83.1, "CAD": 1.36, "AUD": 1.52
                }
                rates = default_rates
                
                # Populate DB for future use
                for curr, rate in default_rates.items():
                    conn.execute(
                        "INSERT INTO currency_rates (base_currency, target_currency, rate, last_updated) VALUES (?, ?, ?, ?)",
                        ("USD", curr, rate, datetime.utcnow().isoformat())
                    )
                conn.commit()
            
            return jsonify({
                "base": "USD",
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "rates": rates
            })
    except Exception as e:
        app.logger.error(f"Currency API error: {e}")
        # Fallback
        return jsonify({
            "base": "USD",
            "rates": {"USD": 1, "EUR": 0.92, "GBP": 0.79}
        })

@app.route("/api/idioms")
def api_idioms():
    """
    Returns weather idioms and cultural sayings.
    """
    lang = request.args.get('lang', 'en')
    condition = request.args.get('condition', 'clear')
    
    try:
        # 1. Try DB first
        idioms = []
        with get_db() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            # Loose matching for condition
            c.execute(
                "SELECT * FROM weather_idioms WHERE language = ? AND condition LIKE ?", 
                (lang, f"%{condition}%")
            )
            idioms = [dict(row) for row in c.fetchall()]
            
        # 2. If no DB results, load from static JSON file as fallback source of truth
        if not idioms:
            json_path = os.path.join(app.root_path, 'assets', 'idioms.json')
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    all_idioms = json.load(f)
                    # Filter logic similar to JS
                    pool = all_idioms.get(condition.lower(), []) or all_idioms.get('clear', [])
                    idioms = [i for i in pool if i.get('language') == lang]
                    if not idioms and lang != 'en':
                        # Fallback to English
                        idioms = [i for i in pool if i.get('language') == 'en']

        return jsonify(idioms)
    except Exception as e:
        app.logger.error(f"Idioms API error: {e}")
        return jsonify([])

# ============================================================================
# Smart Home Integration API Endpoints
# ============================================================================

@app.route("/api/smarthome/register", methods=["POST"])
@limiter.limit("10 per hour")
def api_smarthome_register():
    """Register a new smart home device."""
    if 'user_email' not in session:
        return jsonify({"error": "Unauthorized. Please log in."}), 401
    
    data = request.get_json(silent=True) or {}
    device_name = data.get("device_name")
    device_type = data.get("device_type", "custom")
    lat = data.get("lat")
    lon = data.get("lon")
    preferences = data.get("preferences", {})
    
    if not device_name:
        return jsonify({"error": "Device name is required"}), 400
    
    try:
        email = session['user_email']
        api_key = utils.generate_api_key()
        
        with get_db() as conn:
            conn.execute("""
                INSERT INTO smart_devices 
                (email, device_name, device_type, api_key, lat, lon, preferences, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                email,
                device_name,
                device_type,
                api_key,
                lat,
                lon,
                json.dumps(preferences),
                datetime.utcnow().isoformat()
            ))
            conn.commit()
            
            device_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        return jsonify({
            "success": True,
            "device_id": device_id,
            "api_key": api_key,
            "message": "Device registered successfully"
        })
        
    except Exception as e:
        app.logger.error(f"Device registration error: {e}")
        return jsonify({"error": "Failed to register device"}), 500

@app.route("/api/smarthome/devices", methods=["GET"])
def api_smarthome_devices():
    """List user's registered smart home devices."""
    if 'user_email' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        email = session['user_email']
        
        with get_db() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, device_name, device_type, api_key, lat, lon, 
                       created_at, last_accessed
                FROM smart_devices
                WHERE email = ?
                ORDER BY created_at DESC
            """, (email,))
            
            devices = []
            for row in cursor.fetchall():
                device = dict(row)
                # Mask API key for security (show only last 8 chars)
                device['api_key_masked'] = '...' + device['api_key'][-8:]
                device['api_key_full'] = device['api_key']  # Include full key for copy
                devices.append(device)
        
        return jsonify(devices)
        
    except Exception as e:
        app.logger.error(f"Device list error: {e}")
        return jsonify({"error": "Failed to fetch devices"}), 500

@app.route("/api/smarthome/devices/<int:device_id>", methods=["DELETE"])
def api_smarthome_delete_device(device_id):
    """Delete a registered device."""
    if 'user_email' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        email = session['user_email']
        
        with get_db() as conn:
            # Verify ownership before deleting
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM smart_devices WHERE id = ? AND email = ?", (device_id, email))
            if not cursor.fetchone():
                return jsonify({"error": "Device not found or unauthorized"}), 404
            
            conn.execute("DELETE FROM smart_devices WHERE id = ? AND email = ?", (device_id, email))
            conn.commit()
        
        return jsonify({"success": True, "message": "Device deleted successfully"})
        
    except Exception as e:
        app.logger.error(f"Device deletion error: {e}")
        return jsonify({"error": "Failed to delete device"}), 500

@app.route("/api/smarthome/weather", methods=["GET"])
@limiter.limit("60 per hour")
def api_smarthome_weather():
    """Weather data endpoint for smart home devices (requires API key)."""
    # Check for API key in header or query param
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    
    if not api_key:
        return jsonify({"error": "API key required"}), 401
    
    try:
        with get_db() as conn:
            device = utils.verify_api_key(api_key, conn)
            
            if not device:
                return jsonify({"error": "Invalid API key"}), 401
            
            # Use device's registered location or provided lat/lon
            lat = request.args.get('lat') or device.get('lat')
            lon = request.args.get('lon') or device.get('lon')
            
            if not lat or not lon:
                return jsonify({"error": "Location required"}), 400
            
            # Fetch weather data
            current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
            resp = requests.get(current_url, timeout=5)
            resp.raise_for_status()
            weather_data = resp.json()
            
            # Return compact format optimized for devices
            return jsonify({
                "location": {
                    "city": weather_data.get("name", "Unknown"),
                    "country": weather_data.get("sys", {}).get("country", ""),
                    "lat": lat,
                    "lon": lon
                },
                "current": {
                    "temp": round(weather_data["main"]["temp"], 1),
                    "feels_like": round(weather_data["main"]["feels_like"], 1),
                    "humidity": weather_data["main"]["humidity"],
                    "pressure": weather_data["main"]["pressure"],
                    "weather": {
                        "main": weather_data["weather"][0]["main"],
                        "description": weather_data["weather"][0]["description"],
                        "icon": weather_data["weather"][0]["icon"]
                    },
                    "wind_speed": round(weather_data["wind"]["speed"], 1)
                },
                "timestamp": int(datetime.utcnow().timestamp()),
                "device": {
                    "name": device.get("device_name"),
                    "type": device.get("device_type")
                }
            })
            
    except Exception as e:
        app.logger.error(f"Smart home weather error: {e}")
        return jsonify({"error": "Failed to fetch weather data"}), 500

@app.route("/api/smarthome/alerts", methods=["GET"])
@limiter.limit("30 per hour")
def api_smarthome_alerts():
    """Active weather alerts for smart home devices."""
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    
    if not api_key:
        return jsonify({"error": "API key required"}), 401
    
    try:
        with get_db() as conn:
            device = utils.verify_api_key(api_key, conn)
            
            if not device:
                return jsonify({"error": "Invalid API key"}), 401
            
            lat = device.get('lat')
            lon = device.get('lon')
            
            if not lat or not lon:
                return jsonify({"error": "Device location not configured"}), 400
            
            # Fetch alerts from OpenWeatherMap
            alert_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly,daily&appid={OPENWEATHER_API_KEY}"
            resp = requests.get(alert_url, timeout=5)
            
            if resp.ok:
                data = resp.json()
                alerts = data.get('alerts', [])
                
                return jsonify({
                    "alerts": alerts,
                    "count": len(alerts),
                    "location": {
                        "lat": lat,
                        "lon": lon
                    }
                })
            else:
                return jsonify({"alerts": [], "count": 0})
                
    except Exception as e:
        app.logger.error(f"Smart home alerts error: {e}")
        return jsonify({"error": "Failed to fetch alerts"}), 500

# ============================================================================
# Webhook Integration API Endpoints
# ============================================================================

@app.route("/api/webhooks/subscribe", methods=["POST"])
@limiter.limit("10 per hour")
def api_webhook_subscribe():
    """Register a new webhook subscription."""
    if 'user_email' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json(silent=True) or {}
    webhook_url = data.get("webhook_url")
    event_types = data.get("event_types", [])
    lat = data.get("lat")
    lon = data.get("lon")
    secret_token = data.get("secret_token")
    
    if not webhook_url or not event_types:
        return jsonify({"error": "Webhook URL and event types are required"}), 400
    
    if not lat or not lon:
        return jsonify({"error": "Location (lat/lon) is required"}), 400
    
    # Validate event types
    valid_events = ['weather_alert', 'daily_forecast', 'condition_change']
    if not all(e in valid_events for e in event_types):
        return jsonify({"error": f"Invalid event types. Valid: {valid_events}"}), 400
    
    try:
        email = session['user_email']
        
        # Test webhook connectivity
        test_payload = {
            "event_type": "test",
            "message": "SynoCast webhook subscription test",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        success, error = utils.send_webhook(webhook_url, test_payload, secret_token, max_retries=1)
        
        if not success:
            return jsonify({
                "error": f"Webhook test failed: {error}",
                "suggestion": "Please verify the URL is accessible and accepts POST requests"
            }), 400
        
        with get_db() as conn:
            conn.execute("""
                INSERT INTO webhook_subscriptions
                (email, webhook_url, event_types, lat, lon, secret_token, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                email,
                webhook_url,
                json.dumps(event_types),
                lat,
                lon,
                secret_token,
                datetime.utcnow().isoformat()
            ))
            conn.commit()
            
            subscription_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        return jsonify({
            "success": True,
            "subscription_id": subscription_id,
            "message": "Webhook subscribed successfully"
        })
        
    except Exception as e:
        app.logger.error(f"Webhook subscription error: {e}")
        return jsonify({"error": "Failed to subscribe webhook"}), 500

@app.route("/api/webhooks/subscriptions", methods=["GET"])
def api_webhook_subscriptions():
    """List user's webhook subscriptions."""
    if 'user_email' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        email = session['user_email']
        
        with get_db() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, webhook_url, event_types, lat, lon, is_active,
                       created_at, last_triggered, failure_count
                FROM webhook_subscriptions
                WHERE email = ?
                ORDER BY created_at DESC
            """, (email,))
            
            subscriptions = []
            for row in cursor.fetchall():
                sub = dict(row)
                sub['event_types'] = json.loads(sub['event_types'])
                subscriptions.append(sub)
        
        return jsonify(subscriptions)
        
    except Exception as e:
        app.logger.error(f"Webhook list error: {e}")
        return jsonify({"error": "Failed to fetch subscriptions"}), 500

@app.route("/api/webhooks/subscriptions/<int:sub_id>", methods=["DELETE"])
def api_webhook_delete(sub_id):
    """Delete a webhook subscription."""
    if 'user_email' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        email = session['user_email']
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM webhook_subscriptions WHERE id = ? AND email = ?", (sub_id, email))
            if not cursor.fetchone():
                return jsonify({"error": "Subscription not found"}), 404
            
            conn.execute("DELETE FROM webhook_subscriptions WHERE id = ? AND email = ?", (sub_id, email))
            conn.commit()
        
        return jsonify({"success": True, "message": "Webhook deleted successfully"})
        
    except Exception as e:
        app.logger.error(f"Webhook deletion error: {e}")
        return jsonify({"error": "Failed to delete webhook"}), 500

@app.route("/api/webhooks/test", methods=["POST"])
@limiter.limit("5 per minute")
def api_webhook_test():
    """Test a webhook delivery."""
    if 'user_email' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json(silent=True) or {}
    subscription_id = data.get("subscription_id")
    
    if not subscription_id:
        return jsonify({"error": "Subscription ID required"}), 400
    
    try:
        email = session['user_email']
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT webhook_url, secret_token
                FROM webhook_subscriptions
                WHERE id = ? AND email = ?
            """, (subscription_id, email))
            
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": "Subscription not found"}), 404
            
            webhook_url, secret_token = row
            
            test_payload = {
                "event_type": "test",
                "message": "This is a test webhook from SynoCast",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "subscription_id": subscription_id
            }
            
            success, error = utils.send_webhook(webhook_url, test_payload, secret_token)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": "Test webhook delivered successfully"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": f"Webhook delivery failed: {error}"
                }), 400
                
    except Exception as e:
        app.logger.error(f"Webhook test error: {e}")
        return jsonify({"error": "Failed to test webhook"}), 500

# ============================================================================
# Voice Assistant Integration API Endpoints
# ============================================================================

@app.route("/api/voice/alexa", methods=["POST"])
@csrf.exempt  # Alexa requests won't have CSRF token
@limiter.limit("100 per minute")
def api_voice_alexa():
    """Alexa Skill backend endpoint."""
    try:
        alexa_request = request.get_json()
        
        # Extract intent and slots
        request_type = alexa_request.get('request', {}).get('type')
        
        if request_type == 'LaunchRequest':
            return jsonify({
                "version": "1.0",
                "response": {
                    "outputSpeech": {
                        "type": "PlainText",
                        "text": "Welcome to SynoCast! Ask me about the weather in any city."
                    },
                    "shouldEndSession": False
                }
            })
        
        if request_type == 'IntentRequest':
            intent_name = alexa_request.get('request', {}).get('intent', {}).get('name')
            slots = alexa_request.get('request', {}).get('intent', {}).get('slots', {})
            
            # Extract city from slot
            city = slots.get('city', {}).get('value', 'London')
            
            # Geocode city
            geo_url = f"https://nominatim.openstreetmap.org/search?format=json&q={city}&limit=1"
            headers = {'User-Agent': 'SynoCast/1.0'}
            geo_res = requests.get(geo_url, headers=headers, timeout=5)
            
            if not geo_res.ok or not geo_res.json():
                return jsonify({
                    "version": "1.0",
                    "response": {
                        "outputSpeech": {
                            "type": "PlainText",
                            "text": f"Sorry, I couldn't find weather information for {city}."
                        },
                        "shouldEndSession": True
                    }
                })
            
            loc = geo_res.json()[0]
            lat, lon = loc['lat'], loc['lon']
            
            # Fetch weather
            weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
            weather_res = requests.get(weather_url, timeout=5)
            weather_res.raise_for_status()
            weather_data = weather_res.json()
            
            # Format response
            formatted_data = {
                "location": {"city": city},
                "current": {
                    "temp": weather_data["main"]["temp"],
                    "weather": {
                        "description": weather_data["weather"][0]["description"]
                    }
                }
            }
            
            return jsonify(utils.format_alexa_response(formatted_data))
        
        # Default response
        return jsonify({
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "I didn't understand that request."
                },
                "shouldEndSession": True
            }
        })
        
    except Exception as e:
        app.logger.error(f"Alexa endpoint error: {e}")
        return jsonify({
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "Sorry, I'm having trouble right now. Please try again later."
                },
                "shouldEndSession": True
            }
        })

@app.route("/api/voice/google", methods=["POST"])
@csrf.exempt  # Google Actions requests won't have CSRF token
@limiter.limit("100 per minute")
def api_voice_google():
    """Google Actions backend endpoint."""
    try:
        google_request = request.get_json()
        
        # Extract query parameters
        query_result = google_request.get('queryResult', {})
        parameters = query_result.get('parameters', {})
        city = parameters.get('geo-city', 'London')
        
        # Geocode city
        geo_url = f"https://nominatim.openstreetmap.org/search?format=json&q={city}&limit=1"
        headers = {'User-Agent': 'SynoCast/1.0'}
        geo_res = requests.get(geo_url, headers=headers, timeout=5)
        
        if not geo_res.ok or not geo_res.json():
            return jsonify({
                "fulfillmentText": f"Sorry, I couldn't find weather information for {city}."
            })
        
        loc = geo_res.json()[0]
        lat, lon = loc['lat'], loc['lon']
        
        # Fetch weather
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
        weather_res = requests.get(weather_url, timeout=5)
        weather_res.raise_for_status()
        weather_data = weather_res.json()
        
        # Format response
        formatted_data = {
            "location": {"city": city},
            "current": {
                "temp": weather_data["main"]["temp"],
                "weather": {
                    "description": weather_data["weather"][0]["description"]
                }
            }
        }
        
        return jsonify(utils.format_google_response(formatted_data))
        
    except Exception as e:
        app.logger.error(f"Google Actions endpoint error: {e}")
        return jsonify({
            "fulfillmentText": "Sorry, I'm having trouble right now. Please try again later."
        })

# --- Gamification and Community APIs ---

def check_report_accuracy(reported_condition, lat, lon):
    """
    Verifies user report against OpenWeatherMap current data.
    Returns: (is_accurate, score_bonus)
    """
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
        res = requests.get(url, timeout=5)
        if not res.ok: 
            return False, 0
        
        data = res.json()
        api_main = data['weather'][0]['main'].lower()
        api_desc = data['weather'][0]['description'].lower()
        reported = reported_condition.lower()

        # Simple mapping for matching
        match = False
        if reported in api_desc or reported in api_main:
            match = True
        elif reported == "clear" and "clear" in api_main:
            match = True
        elif reported == "cloudy" and "cloud" in api_main:
            match = True
        elif reported in ["rain", "drizzle"] and ("rain" in api_main or "drizzle" in api_main):
            match = True
        
        return match, (50 if match else 0)
    except Exception as e:
        app.logger.error(f"Accuracy check failed: {e}")
        return False, 0

def award_points(email, points, event_type, description):
    """Helper to add points and check for badges."""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO user_points (email, points, event_type, description, created_at) VALUES (?, ?, ?, ?, ?)",
            (email, points, event_type, description, datetime.utcnow().isoformat())
        )
        conn.commit()
    
    # Check for point-based badges (e.g. Community Pillar > 500)
    # This logic can be expanded.

@app.route("/api/community/report", methods=["POST"])
def api_submit_report():
    if 'user_email' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    email = session['user_email']
    data = request.json
    lat = data.get('lat')
    lon = data.get('lon')
    condition = data.get('condition')
    
    if not lat or not lon or not condition:
        return jsonify({"error": "Missing data"}), 400

    # 1. Verify Accuracy
    is_accurate, bonus_points = check_report_accuracy(condition, lat, lon)
    
    # 2. Save Report
    with get_db() as conn:
        conn.execute(
            "INSERT INTO weather_reports (lat, lon, city, reported_condition, reported_at, is_accurate, api_condition, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (lat, lon, "Unknown", condition, datetime.utcnow().isoformat(), 1 if is_accurate else 0, "verified_api", email)
        )
        conn.commit()
    
    # 3. Award Points
    base_points = 10
    total_points = base_points + bonus_points
    desc = f"Weather Report: {condition} ({'Accurate' if is_accurate else 'Unverified'})"
    award_points(email, total_points, 'report_submission', desc)
    
    # 4. Check & Award Badges (Reliable Source)
    new_badge = None
    if is_accurate:
        with get_db() as conn:
            # Count accurate reports
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM weather_reports WHERE is_accurate=1 AND email=?", (email,)) 
            count = c.fetchone()[0]
            
            if count >= 5:
                # Check if already has badge
                c.execute("SELECT id FROM badges WHERE name='Reliable Source'")
                badge_row = c.fetchone()
                if badge_row:
                    badge_id = badge_row[0]
                    try:
                        conn.execute("INSERT INTO user_badges (email, badge_id, awarded_at) VALUES (?, ?, ?)", (email, badge_id, datetime.utcnow().isoformat()))
                        conn.commit()
                        new_badge = "Reliable Source"
                    except sqlite3.IntegrityError:
                        pass # Already has it

    return jsonify({
        "success": True, 
        "points_earned": total_points, 
        "verified": is_accurate,
        "new_badge": new_badge,
        "message": f"Report submitted! {total_points} points earned." + (f" New Badge: {new_badge}!" if new_badge else "")
    })

@app.route("/api/community/leaderboard")
def api_leaderboard():
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        # Sum points by user
        c.execute("""
            SELECT email, SUM(points) as total_score 
            FROM user_points 
            GROUP BY email 
            ORDER BY total_score DESC 
            LIMIT 10
        """)
        leaders = [dict(row) for row in c.fetchall()]
        
        # Mask emails for privacy (e.g. "afn... @gmail.com")
        for l in leaders:
            parts = l['email'].split('@')
            if len(parts) == 2:
                l['display_name'] = f"{parts[0][:3]}...@{parts[1]}"
            else:
                l['display_name'] = "User"
            del l['email']
            
    return jsonify(leaders)

@app.route("/api/user/badges")
def api_user_badges():
    if 'user_email' not in session:
        return jsonify({"earned": [], "all": [], "total_points": 0})
    
    email = session['user_email']
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get Badges
        c.execute("""
            SELECT b.name, b.description, b.icon_class, ub.awarded_at 
            FROM user_badges ub
            JOIN badges b ON ub.badge_id = b.id
            WHERE ub.email = ?
        """, (email,))
        earned = [dict(row) for row in c.fetchall()]
        
        # Get All Badges
        c.execute("SELECT name, description, icon_class, threshold FROM badges")
        all_badges = [dict(row) for row in c.fetchall()]
        
        # Get Total Points
        c.execute("SELECT SUM(points) FROM user_points WHERE email = ?", (email,))
        res = c.fetchone()
        total = res[0] if res and res[0] else 0
        
    return jsonify({"earned": earned, "all": all_badges, "total_points": total})


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
    
    # Handle Rate Limit errors specifically
    if "Too Many Requests" in str(e) or (hasattr(e, 'code') and e.code == 429):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Rate limit exceeded. Please slow down."}), 429
        return render_template("500.html", message="Too many requests. Please try again later.", date_time_info=utils.get_local_time_string(), active_page="404"), 429

    if request.path.startswith('/api/'):
        # Check if it's a known error from Gemini or other APIs
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg:
            return jsonify({"error": "Invalid API Key for AI service"}), 500
        return jsonify({"error": f"An unexpected error occurred: {error_msg}"}), 500
    # Fallback to 500 page for generic exceptions
    return render_template("500.html", date_time_info=utils.get_local_time_string(), active_page="404"), 500

if __name__ == "__main__":
    # Start weather alert background task (only in local development)
    # Note: Background threads don't work on Vercel's serverless platform
    if not os.environ.get("VERCEL"):
        alert_thread = threading.Thread(target=check_weather_alerts, daemon=True)
        alert_thread.start()
        
        daily_thread = threading.Thread(target=trigger_daily_forecast_webhooks, daemon=True)
        daily_thread.start()
    app.run(debug=True)