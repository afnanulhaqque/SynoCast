import os
import sqlite3
import requests
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
DATABASE = os.path.join(app.root_path, "subscriptions.db")


def init_db():
    """Create the subscriptions table if it does not already exist."""
    conn = sqlite3.connect(DATABASE)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
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
        data = requests.get(f"https://ipapi.co/{ip}/json/").json()
        city = data.get("city", "")
        region = data.get("region", "")
        utc_offset = data.get("utc_offset", "0000")

    # 3. Convert offset string (“-0300”) to hours/minutes
    offset_hours = int(utc_offset[:3])     # "-03" -> -3
    offset_minutes = int(utc_offset[3:])   # "00" -> 0

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
    # Very small demo reply — change this to hook up an AI or other chat backend
    reply = f"SynoCast: You said '{message}'"
    return jsonify({'reply': reply})


@app.route("/otp", methods=["POST"])
def otp():
    action = request.form.get("action")
    email = session.get("pending_email")

    if action == "request":
        submitted_email = request.form.get("email")
        if not submitted_email:
            return jsonify({"success": False, "message": "Please enter your email address."}), 400

        # Check if email is already subscribed
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM subscriptions WHERE email = ?", (submitted_email,))
        exists = cursor.fetchone()
        conn.close()

        if exists:
            return jsonify({"success": False, "message": "Email is already subscribed"}), 400

        session["pending_email"] = submitted_email
        return jsonify({"success": True, "step": "otp", "email": submitted_email})

    if action == "verify":
        submitted_otp = request.form.get("otp", "").strip()
        if not email:
            return jsonify({"success": False, "message": "Session expired. Please start again."}), 400

        if submitted_otp == EXPECTED_OTP:
            session.pop("pending_email", None)
            conn = sqlite3.connect(DATABASE)
            conn.execute(
                "INSERT INTO subscriptions (email, created_at) VALUES (?, ?)",
                (email, datetime.utcnow().isoformat()),
            )
            conn.commit()
            conn.close()
            return jsonify({"success": True, "step": "success"})

        return jsonify({"success": False, "message": "Incorrect OTP. Please try again."}), 400

    return jsonify({"success": False, "message": "Invalid action."}), 400


if __name__ == "__main__":
    app.run(debug=True)