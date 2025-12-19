import os
import sqlite3
import requests
import random
import resend
import concurrent.futures
from flask import Flask, render_template, request, session, jsonify
from datetime import datetime, timedelta, timezone
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="assests",
    static_url_path="/assests",
)
app.secret_key = "synocast-dev-secret"

# Simple in-memory cache for weather data
# Key: f"{lat},{lon}"
# Value: {"timestamp": float, "data": dict}
WEATHER_CACHE = {}
CACHE_DURATION = 600  # 10 minutes in seconds

if os.environ.get("VERCEL"):
    DATABASE = "/tmp/subscriptions.db"
else:
    DATABASE = os.path.join(app.root_path, "subscriptions.db")

# Resend API Key
resend.api_key = os.environ.get("RESEND_API_KEY", "re_5UBuV4Aw_KHWvj2y7YPR4ahvMtwTv561V")

# OpenWeatherMap API Key
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "1254601d1d95a31977b5b19d0c989a93")

def init_db():
    """Create the subscriptions table if it does not already exist and handle migrations."""
    conn = sqlite3.connect(DATABASE)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            phone TEXT,
            subscription_type TEXT DEFAULT 'email',
            created_at TEXT NOT NULL
        )
        """
    )
    # Attempt to add columns if they don't exist (for existing databases)
    try:
        conn.execute("ALTER TABLE subscriptions ADD COLUMN phone TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE subscriptions ADD COLUMN subscription_type TEXT DEFAULT 'email'")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()


# Flask 3.x no longer provides `before_first_request` on the app instance.
# Initialize the DB at import time so we don't rely on a lifecycle hook that
# may not be present across different Flask versions / servers.
try:
    init_db()
except Exception as e:
    # If initialization fails, log it; apps running under other servers will
    # pick this up in their logs as well.
    try:
        app.logger.exception("Database initialization failed: %s", e)
    except Exception:
        # If app.logger itself isn't ready, fallback to printing to stdout
        print("Database initialization failed:", e)

def get_local_time_string():
    # 1. Get user IP address first
    ip = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0]
    
    # Check session for cached location data
    if "location_data" in session and session["location_data"].get("ip") == ip:
        data = session["location_data"]
        city = data.get("city", "Unknown")
        region = data.get("region", "")
        utc_offset = data.get("utc_offset", "+0000")
    else:
        if ip.startswith("127.") or ip == "localhost":
            city = "Islamabad"
            region = "Punjab"
            utc_offset = "+0500"
            # Cache local dev defaults too
            session["location_data"] = {
                "ip": ip,
                "city": city,
                "region": region,
                "utc_offset": utc_offset
            }
        else:
            # 2. Fetch IP info
            try:
                # Reduced timeout to fail faster
                resp = requests.get(f"https://ipapi.co/{ip}/json/", timeout=2)
                resp.raise_for_status()
                data = resp.json()
                city = data.get("city", "")
                region = data.get("region", "")
                utc_offset = data.get("utc_offset", "+0000")
                
                # Cache successful lookup
                session["location_data"] = {
                    "ip": ip,
                    "city": city,
                    "region": region,
                    "utc_offset": utc_offset
                }
            except:
                city = "Unknown"
                region = ""
                utc_offset = "+0000"

    # 3. Convert offset string (“-0300”) to hours/minutes
    try:
        offset_hours = int(utc_offset[:3])     # "-03" -> -3
        offset_minutes = int(utc_offset[3:])   # "00" -> 0
    except:
        offset_hours = 0
        offset_minutes = 0

    tz = timezone(timedelta(hours=offset_hours, minutes=offset_minutes))

    # 4. Local time = now in that timezone
    now = datetime.now(tz)

    # 5. Format like your example
    formatted = now.strftime("%A, %B %d, %Y, %H:%M")

    # 6. Convert offset to GMT format: "-0300" → "GMT-03:00"
    gmt_offset = f"GMT{utc_offset[:3]}:{utc_offset[3:]}"

    full_string =  f"{formatted} Time zone in {city} - {region} ({gmt_offset})"

    return {
        "display_string": full_string,
        "city": city,
        "region": region,
        "utc_offset": utc_offset, # e.g. "+0500"
        "gmt_label": gmt_offset   # e.g. "GMT+05:00"
    }

@app.route("/")
def home():
    return render_template("home.html", active_page="home", date_time_info=get_local_time_string())


@app.route("/news")
def news():
    return render_template("news.html", active_page="news", date_time_info=get_local_time_string())


@app.route("/weather")
def weather():
    return render_template("weather.html", active_page="weather", date_time_info=get_local_time_string())


@app.route("/subscribe")
def subscribe():
    return render_template("subscribe.html", active_page="subscribe", date_time_info=get_local_time_string())


@app.route("/about")
def about():
    return render_template("about.html", active_page="about", date_time_info=get_local_time_string())


@app.route("/terms")
def terms():
    return render_template("terms.html", active_page="terms", date_time_info=get_local_time_string())



@app.route("/api/weather")
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

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_current = executor.submit(requests.get, current_url, timeout=5)
            future_forecast = executor.submit(requests.get, forecast_url, timeout=5)

            current_res = future_current.result()
            forecast_res = future_forecast.result()

        current_res.raise_for_status()
        forecast_res.raise_for_status()

        current_data = current_res.json()
        forecast_data = forecast_res.json()

        result = {
            "current": current_data,
            "forecast": forecast_data
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


@app.route("/api/geocode/search")
def geocode_search():
    """Proxy endpoint for Nominatim forward geocoding (search)."""
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    
    try:
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={query}"
        headers = {'User-Agent': 'SynoCast/1.0'}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        app.logger.error(f"Geocode search error: {e}")
        return jsonify({"error": "Failed to fetch location data"}), 500


@app.route("/api/geocode/reverse")
def geocode_reverse():
    """Proxy endpoint for Nominatim reverse geocoding."""
    lat = request.args.get('lat', '')
    lon = request.args.get('lon', '')
    
    if not lat or not lon:
        return jsonify({"error": "Parameters 'lat' and 'lon' are required"}), 400
    
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
        headers = {'User-Agent': 'SynoCast/1.0'}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        app.logger.error(f"Reverse geocode error: {e}")
        return jsonify({"error": "Failed to fetch location data"}), 500


@app.route("/otp", methods=["POST"])
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

            # Check if already subscribed
            try:
                conn = sqlite3.connect(DATABASE)
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM subscriptions WHERE email = ?", (contact_info,))
                exists = cursor.fetchone()
                conn.close()
            except sqlite3.OperationalError as e:
                # If table is missing, try to create it (recovery)
                if "no such table" in str(e):
                    init_db()
                    conn = sqlite3.connect(DATABASE)
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1 FROM subscriptions WHERE email = ?", (contact_info,))
                    exists = cursor.fetchone()
                    conn.close()
                else:
                    raise e

            if exists:
                return jsonify({"success": False, "message": "Email is already subscribed"}), 400

            # Generate OTP
            otp_code = "".join([str(random.randint(0, 9)) for _ in range(6)])
            session["expected_otp"] = otp_code
            session["pending_contact"] = contact_info
            session["pending_type"] = sub_type

            # Send OTP (Email)
            try:
                # Using onboarding@resend.dev as the sender to ensure delivery without domain verification.
                # The user's email is set as Reply-To.
                r = resend.Emails.send({
                    "from": "SynoCast <onboarding@resend.dev>", 
                    "to": contact_info,
                    "reply_to": "afnanulhaq4@gmail.com",
                    "subject": "Your SynoCast Subscription OTP",
                    "html": f"""
                    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                        <h2 style="color: #333;">Welcome to SynoCast!</h2>
                        <p>Thank you for subscribing to SynoCast. Please use the following One-Time Password (OTP) to complete your subscription:</p>
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
                session.pop("pending_contact", None)
                session.pop("expected_otp", None)
                session.pop("pending_type", None)
                
                conn = sqlite3.connect(DATABASE)
                conn.execute(
                    "INSERT INTO subscriptions (email, subscription_type, created_at) VALUES (?, ?, ?)",
                    (contact_info, sub_type, datetime.utcnow().isoformat()),
                )
                conn.commit()
                conn.close()
                return jsonify({"success": True, "step": "success"})

            return jsonify({"success": False, "message": "Incorrect OTP. Please try again."}), 400

        return jsonify({"success": False, "message": "Invalid action."}), 400
    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return jsonify({"success": False, "message": "An internal server error occurred."}), 500


@app.route("/api/ai_chat", methods=["POST"])
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

    # Initialize weather context
    weather_context = ""
    
    # If lat/lon not in request, try to get them via IP
    if not (lat and lon):
        try:
            ip = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0]
            if ip.startswith("127.") or ip == "localhost":
                # Default to Islamabad for local development
                lat, lon = 33.6844, 73.0479
            else:
                resp_ip = requests.get(f"https://ipapi.co/{ip}/json/", timeout=2)
                if resp_ip.ok:
                    ip_data = resp_ip.json()
                    lat = ip_data.get("latitude")
                    lon = ip_data.get("longitude")
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
        "If CURRENT WEATHER CONTEXT is provided below, use it to answer directly. "
        "NEVER ask for the user's city, zip code, or location if the context is already provided. "
        "For example, if asked 'Should I carry an umbrella?' and it's raining in the context, say 'Yes, it is raining in [City] right now'. "
        "Only if context is completely missing should you ask for their location."
    )

    # Use environment variable for Gemini API key
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    
    if not gemini_api_key:
         return jsonify({"error": "Server configuration error: Gemini API Key missing."}), 500

    try:
        # Strip the key to ensure no whitespace/newlines cause issues
        gemini_api_key = gemini_api_key.strip()
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        
        full_prompt = f"{system_prompt}{weather_context}\n\nUser: {user_message}"
        
        response = model.generate_content(full_prompt)
        
        if response.text:
             return jsonify({"reply": response.text})
        else:
             return jsonify({"reply": "I'm sorry, I couldn't generate a response."})

    except Exception as e:
        app.logger.error(f"Gemini API error: {e}")
        return jsonify({"error": f"Failed to process request: {str(e)}"}), 500



@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", date_time_info=get_local_time_string(), active_page="404"), 404

from jinja2.exceptions import TemplateSyntaxError

@app.errorhandler(500)
def internal_error(e):
    if request.path.startswith('/api/'):
        return jsonify({"error": "Internal server error occurred"}), 500
    return render_template("500.html", date_time_info=get_local_time_string(), active_page="404"), 500


@app.errorhandler(TemplateSyntaxError)
def syntax_error(e):
    return render_template("syntax_error.html"), 500


@app.errorhandler(Exception)
def unhandled_exception(e):
    app.logger.error(f"Unhandled Exception: {e}")
    if request.path.startswith('/api/'):
        # Check if it's a known error from Gemini or other APIs
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg:
            return jsonify({"error": "Invalid API Key for AI service"}), 500
        return jsonify({"error": f"An unexpected error occurred: {error_msg}"}), 500
    # Fallback to 500 page for generic exceptions
    return render_template("500.html", date_time_info=get_local_time_string(), active_page="404"), 500

if __name__ == "__main__":
    app.run(debug=True)