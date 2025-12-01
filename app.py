import os
import sqlite3
import requests
import random
import resend
from flask import Flask, render_template, request, session, jsonify
from datetime import datetime, timedelta, timezone

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="assests",
    static_url_path="/assests",
)
app.secret_key = "synocast-dev-secret"
EXPECTED_OTP = "123456"
if os.environ.get("VERCEL"):
    DATABASE = "/tmp/subscriptions.db"
else:
    DATABASE = os.path.join(app.root_path, "subscriptions.db")

# Resend API Key
resend.api_key = "re_5UBuV4Aw_KHWvj2y7YPR4ahvMtwTv561V"

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
    if ip.startswith("127.") or ip == "localhost":
        city = "Islamabad"
        region = "Punjab"
        utc_offset = "+0500"
    else:
        # 2. Fetch IP info
        try:
            data = requests.get(f"https://ipapi.co/{ip}/json/", timeout=5).json()
            city = data.get("city", "")
            region = data.get("region", "")
            utc_offset = data.get("utc_offset", "0000")
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


@app.route("/chatbot")
def chatbot():
    # We don't have a dedicated chatbot page template; render the home template and
    # rely on the modal instead (it is available on base.html).
    return render_template("home.html", active_page="chatbot", date_time_info=get_local_time_string())


@app.route('/chat', methods=['POST'])
def chat_api():
    """A very lightweight chat endpoint returning a JSON reply.
    For now, the server simply returns an echo-like reply for demonstration.
    """
    data = request.get_json(silent=True) or {}
    message = data.get('message', '')
    if not message:
        return jsonify({'reply': "Please send a message."}), 400
    # Mock reply
    reply = f"SynoCast: You said '{message}'"
    return jsonify({'reply': reply})


@app.route("/test_email")
def test_email():
    """
    Test endpoint to verify email sending capabilities.
    Sends a test email to the provided address (or defaults to the verified one).
    Usage: /test_email?email=user@example.com
    """
    try:
        # Get email from query param or default to verified email
        test_recipient = request.args.get('email', 'afnanulhaq4@gmail.com')
        
        r = resend.Emails.send({
            "from": "SynoCast <onboarding@resend.dev>",
            "to": test_recipient,
            "reply_to": "afnanulhaq4@gmail.com",
            "subject": "SynoCast Email Test",
            "html": f"""
            <div style="font-family: sans-serif; padding: 20px;">
                <h2>Email System Check</h2>
                <p>This is a test email to verify that the SynoCast email system is working correctly.</p>
                <p>Sent to: {test_recipient}</p>
                <p>Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            """
        })
        return jsonify({"success": True, "message": f"Test email sent to {test_recipient}", "id": r['id']})
    except Exception as e:
        app.logger.error(f"Test email failed: {e}")
        return jsonify({"success": False, "message": str(e)}), 500



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


if __name__ == "__main__":
    app.run(debug=True)