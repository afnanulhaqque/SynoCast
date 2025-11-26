import requests
from flask import Flask, render_template , request
from datetime import datetime, timedelta, timezone

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="assests",
    static_url_path="/assests",
)

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

    return f"{formatted} Time zone in {city} - {region} ({gmt_offset})"

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
    return render_template("chatbot.html", active_page="chatbot", date_time_info=get_local_time_string())

if __name__ == "__main__":
    app.run(debug=True)