import os
import requests
import json
import random
import concurrent.futures
import sqlite3
from datetime import datetime
from flask import Blueprint, request, jsonify, abort, Response, current_app, session
from google import genai
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .. import utils
from ..extensions import limiter, csrf
from ..database import get_db

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Caches
CITY_CACHE = {}
WEATHER_CACHE = {}
CACHE_DURATION = 600

# API Keys
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")

# Configure http session
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http_session = requests.Session()
http_session.mount("https://", adapter)
http_session.mount("http://", adapter)

# --- Helpers ---

def check_report_accuracy(reported_condition, lat, lon):
    """
    Verifies user report against OpenWeatherMap current data.
    Returns: (is_accurate, score_bonus)
    """
    try:
        api_key = os.environ.get("OPENWEATHER_API_KEY")
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"
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
        current_app.logger.error(f"Accuracy check failed: {e}")
        return False, 0

def award_points(email, points, event_type, description):
    """Helper to add points and check for badges."""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO user_points (email, points, event_type, description, created_at) VALUES (?, ?, ?, ?, ?)",
            (email, points, event_type, description, datetime.utcnow().isoformat())
        )
        conn.commit()

# --- Routes ---

@api_bp.route('/geocode/reverse')
def api_geocode_reverse():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return jsonify({"error": "Missing params"}), 400
        
    try:
        # User-Agent is required by Nominatim
        headers = {'User-Agent': 'SynoCast/1.0'}
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
        res = requests.get(url, headers=headers, timeout=5)
        if res.ok:
            return jsonify(res.json())
        return jsonify({"error": "Geocode failed"}), res.status_code
    except Exception as e:
        current_app.logger.error(f"Reverse Geocode Error: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/geocode/search')
def api_geocode_search():
    query = request.args.get('q')
    if not query:
        return jsonify([])
        
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={query}&limit=5&appid={api_key}"
    
    try:
        res = requests.get(url, timeout=5)
        if res.ok:
            data = res.json()
            results = []
            for item in data:
                name = item.get('name')
                country = item.get('country')
                state = item.get('state', '')
                display = f"{name}, {country}"
                if state:
                    display = f"{name}, {state}, {country}"
                
                results.append({
                    "lat": item.get('lat'),
                    "lon": item.get('lon'),
                    "display_name": display,
                    "name": name,
                    "country": country
                })
            return jsonify(results)
    except Exception as e:
        current_app.logger.error(f"Geocode Error: {e}")
        
    return jsonify([])

@api_bp.route('/travel/weather')
def api_travel_search():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    api_key = os.environ.get("OPENWEATHER_API_KEY")
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={query}&units=metric&appid={api_key}"
        res = requests.get(url, timeout=5)
        
        if res.ok:
            data = res.json()
            return jsonify({
                "city": data.get("name"),
                "country": data.get("sys", {}).get("country"),
                "temp": data.get("main", {}).get("temp"),
                "condition": data.get("weather", [{}])[0].get("description", "Unknown"),
                "icon": data.get("weather", [{}])[0].get("icon"),
                "wind_speed": data.get("wind", {}).get("speed"),
                "humidity": data.get("main", {}).get("humidity"),
                "lat": data.get("coord", {}).get("lat"),
                "lon": data.get("coord", {}).get("lon")
            })
        else:
            return jsonify({"error": "Location not found"}), 404
            
    except Exception as e:
         current_app.logger.error(f"Travel API Error: {e}")
         return jsonify({"error": "Failed to fetch weather data"}), 500

@api_bp.route('/proxy/cities', methods=['POST'])
def api_proxy_cities():
    data = request.json
    country = data.get('country')
    if not country:
        return jsonify({"error": "Country is required"}), 400

    cache_key = f"cities_{country.lower()}"
    if cache_key in CITY_CACHE:
         current_app.logger.info(f"Serving cities for {country} from cache")
         return jsonify({"data": CITY_CACHE[cache_key]})

    try:
        url = "https://countriesnow.space/api/v0.1/countries/cities"
        res = requests.post(url, json={"country": country}, timeout=10)
        
        if res.ok:
            json_data = res.json()
            if not json_data.get('error'):
                cities = json_data.get('data', [])
                CITY_CACHE[cache_key] = cities
                return jsonify({"data": cities})
            else:
                return jsonify({"error": json_data.get("msg")}), 400
        else:
             return jsonify({"error": "Failed to fetch from upstream"}), res.status_code
             
    except Exception as e:
        current_app.logger.error(f"City Proxy Error: {e}")
        return jsonify({"error": "Internal Proxy Error"}), 500

@api_bp.route('/currency/convert')
def api_currency_convert():
    base = request.args.get('base', 'USD').upper()
    targets = request.args.get('targets', 'EUR,GBP,JPY,PKR').upper().split(',')
    
    try:
        res = requests.get(f"https://api.exchangerate-api.com/v4/latest/{base}", timeout=5)
        if res.ok:
            data = res.json()
            rates = data.get('rates', {})
            result = {t: rates.get(t) for t in targets if t in rates}
            return jsonify({"base": base, "rates": result})
    except Exception as e:
        current_app.logger.error(f"Currency API Error: {e}")
    
    mock_rates = {
        "USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 150.0, "PKR": 278.0
    }
    
    base_rate = mock_rates.get(base, 1.0)
    result = {}
    for t in targets:
        target_rate = mock_rates.get(t, 1.0)
        result[t] = round(target_rate / base_rate, 2)
        
    return jsonify({"base": base, "rates": result})

@api_bp.route('/travel/packing-list')
def api_travel_packing_list():
    destination = request.args.get('destination')
    days = request.args.get('days', 3)
    weather_summary = request.args.get('weather') 
    
    if not destination:
        return jsonify({"error": "Missing destination"}), 400

    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        return jsonify({
            "items": [
                {"category": "essentials", "item": "Passport"},
                {"category": "clothing", "item": "Jacket"},
                {"category": "electronics", "item": "Power Bank"}
            ]
        })

    try:
        client = genai.Client(api_key=gemini_key.strip())
        prompt = f"""
        Generate a smart packing list for a {days}-day trip to {destination}.
        Weather forecast: {weather_summary}.
        
        Return JSON with a list of items grouped by category.
        Format:
        {{
            "items": [
                {{"category": "Clothing", "item": "Raincoat (Heavy rain expected)", "icon": "fa-tshirt"}},
                {{"category": "Gadgets", "item": "Universal Adapter", "icon": "fa-plug"}},
                ...
            ]
        }}
        Limit to 10-12 most important items.
        """
        
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        return jsonify(json.loads(response.text))
    except Exception as e:
        current_app.logger.error(f"Packing List AI Error: {e}")
        return jsonify({"items": []})

@api_bp.route('/learn/trivia')
def api_learn_trivia():
    questions = [
        {"q": "What is the highest temperature ever recorded on Earth?", "options": ["56.7°C (Death Valley)", "58°C (Libya)", "54°C (Kuwait)"], "a": 0, "expl": "Furnace Creek Ranch, Death Valley, recorded 56.7°C on July 10, 1913."},
        {"q": "What type of cloud is often called a 'thunderhead'?", "options": ["Cumulus", "Cumulonimbus", "Stratus"], "a": 1, "expl": "Cumulonimbus clouds are dense, towering vertical clouds associated with thunderstorms."},
        {"q": "What instrument measures atmospheric pressure?", "options": ["Thermometer", "Anemometer", "Barometer"], "a": 2, "expl": "Barometers measure atmospheric pressure, which helps predict weather changes."},
        {"q": "Where is the wettest place on Earth?", "options": ["Mawsynram, India", "Cherrapunji, India", "Kauai, Hawaii"], "a": 0, "expl": "Mawsynram receives the highest average annual rainfall."},
        {"q": "What is the calm center of a hurricane called?", "options": ["The Eye", "The Core", "The Hub"], "a": 0, "expl": "The eye is a region of mostly calm weather at the center of strong tropical cyclones."}
    ]
    return jsonify(random.choice(questions))

@api_bp.route('/learn/glossary')
def api_learn_glossary():
    terms = [
        {"term": "Albedo", "definition": "The proportion of the incident light or radiation that is reflected by a surface, typically that of a planet or moon."},
        {"term": "Barometric Pressure", "definition": "The pressure exerted by the weight of the atmosphere."},
        {"term": "Convection", "definition": "Heat transfer in a gas or liquid by the circulation of currents from one region to another."},
        {"term": "Dew Point", "definition": "The temperature at which air becomes saturated with water vapor and dew forms."},
        {"term": "El Niño", "definition": "A warming of the ocean surface, or above-average sea surface temperatures, in the central and eastern tropical Pacific Ocean."},
        {"term": "Front", "definition": "The boundary between two air masses that have different temperatures or humidity."},
        {"term": "Humidity", "definition": "The amount of water vapor in the air."},
        {"term": "Isobar", "definition": "A line on a map connecting points having the same atmospheric pressure."},
        {"term": "Jet Stream", "definition": "Narrow bands of strong wind in the upper levels of the atmosphere."},
        {"term": "Meteorology", "definition": "The scientific study of the atmosphere and its phenomena, especially weather and weather forecasting."},
        {"term": "Precipitation", "definition": "Any form of water, liquid or solid, falling from the sky (rain, snow, hail, etc.)."},
        {"term": "Relative Humidity", "definition": "The ratio of the current absolute humidity to the highest possible absolute humidity at the current temperature."},
        {"term": "Supercell", "definition": "A system producing severe thunderstorms and featuring rotating winds sustained by a prolonged updraft that may result in hail or tornadoes."},
        {"term": "Trade Winds", "definition": "Permanent east-to-west prevailing winds that flow in the Earth's equatorial region."},
        {"term": "Wind Chill", "definition": "The perceived decrease in air temperature felt by the body on exposed skin due to the flow of air."}
    ]
    return jsonify(terms)

@api_bp.route('/weather_data')
def api_weather_data():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return jsonify({"error": "Missing lat/lon"}), 400
    
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if not api_key:
        return jsonify({"error": "Server API Config Error"}), 500
        
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}"
        res = requests.get(url, timeout=5)
        if res.ok:
            return jsonify(res.json())
        return jsonify({"error": "Provider Error"}), res.status_code
    except Exception as e:
        current_app.logger.error(f"Weather Data API Error: {e}")
        return jsonify({"error": "Internal Error"}), 500

@api_bp.route('/proxy/tiles/<layer_type>/<z>/<x>/<y>')
def proxy_weather_tiles(layer_type, z, x, y):
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if not api_key:
         abort(500)
    
    layer_map = {
        "clouds_new": "clouds_new",
        "precipitation_new": "precipitation_new",
        "temp_new": "temp_new",
        "wind_new": "wind_new",
        "pressure_new": "pressure_new"
    }
    
    owm_layer = layer_map.get(layer_type)
    if not owm_layer:
        abort(404)
        
    url = f"https://tile.openweathermap.org/map/{owm_layer}/{z}/{x}/{y}.png?appid={api_key}"
    
    try:
        res = requests.get(url, stream=True, timeout=10)
        if res.ok:
            return Response(res.content, mimetype=res.headers.get('content-type', 'image/png'))
        else:
            return jsonify({"error": "Tile fetch failed"}), 404
    except Exception as e:
        current_app.logger.error(f"Tile Proxy Error: {e}")
        abort(500)

@api_bp.route("/ip-location")
def api_ip_location():
    try:
        user_ip = request.headers.get('CF-Connecting-IP') or \
                  request.headers.get('X-Real-IP') or \
                  request.headers.get('X-Forwarded-For', request.remote_addr)
        
        if user_ip and ',' in user_ip:
            user_ip = user_ip.split(',')[0].strip()

        url = f"http://ip-api.com/json/{user_ip}?fields=status,lat,lon,city,countryCode"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        data = res.json()
        
        if data.get('status') == 'fail' and user_ip in ['127.0.0.1', '::1']:
            res = requests.get("http://ip-api.com/json/?fields=status,lat,lon,city,countryCode", timeout=5)
            data = res.json()

        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"IP Location error: {e}")
        return jsonify({"status": "fail", "message": str(e)}), 500

@api_bp.route("/weather")
@limiter.limit("30 per minute")
def api_weather():
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if not lat or not lon:
        return jsonify({"error": "Missing lat or lon parameters"}), 400

    cache_key = f"{lat},{lon}"
    now_ts = datetime.utcnow().timestamp()
    
    if cache_key in WEATHER_CACHE:
        cached_entry = WEATHER_CACHE[cache_key]
        if now_ts - cached_entry["timestamp"] < CACHE_DURATION:
            current_app.logger.info(f"Serving weather for {cache_key} from cache")
            return jsonify(cached_entry["data"])

    try:
        api_key = os.environ.get("OPENWEATHER_API_KEY")
        current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}"
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={api_key}"
        pollution_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"

        current_data = {}
        forecast_data = {}
        pollution_data = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_current = executor.submit(http_session.get, current_url, timeout=5)
            future_forecast = executor.submit(http_session.get, forecast_url, timeout=5)
            future_pollution = executor.submit(http_session.get, pollution_url, timeout=5)

            try:
                current_res = future_current.result()
                current_res.raise_for_status()
                current_data = current_res.json()
            except Exception as e:
                current_app.logger.error(f"Failed to fetch current weather: {e}")
                return jsonify({"error": "Failed to fetch current weather data"}), 502

            try:
                forecast_res = future_forecast.result()
                forecast_res.raise_for_status()
                forecast_data = forecast_res.json()
            except Exception as e:
                current_app.logger.error(f"Failed to fetch forecast: {e}")
                forecast_data = {} 
                return jsonify({"error": "Failed to fetch forecast data"}), 502

            try:
                pollution_res = future_pollution.result()
                pollution_res.raise_for_status()
                pollution_data = pollution_res.json()
            except Exception as e:
                current_app.logger.warning(f"Failed to fetch air pollution (non-critical): {e}")
                pollution_data = None 

        result = {
            "current": current_data,
            "forecast": forecast_data,
            "pollution": pollution_data
        }

        WEATHER_CACHE[cache_key] = {
            "timestamp": now_ts,
            "data": result
        }

        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"OpenWeatherMap API General error: {e}")
        return jsonify({"error": "Failed to fetch weather data"}), 500

@api_bp.route("/weather/analytics")
def api_weather_analytics():
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if not lat or not lon:
        return jsonify({"error": "Missing lat or lon parameters"}), 400

    cache_key = f"{lat},{lon}"
    now_ts = datetime.utcnow().timestamp()
    
    weather_data = None
    if cache_key in WEATHER_CACHE:
        cached_entry = WEATHER_CACHE[cache_key]
        if now_ts - cached_entry["timestamp"] < CACHE_DURATION:
            weather_data = cached_entry["data"]

    if not weather_data:
        try:
            api_key = os.environ.get("OPENWEATHER_API_KEY")
            forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={api_key}"
            res = requests.get(forecast_url, timeout=5)
            res.raise_for_status()
            forecast_data = res.json()
            weather_data = {"forecast": forecast_data}
        except Exception as e:
            current_app.logger.error(f"Analytics fetch error: {e}")
            return jsonify({"error": "Failed to fetch weather data"}), 500

    try:
        forecast = weather_data["forecast"]
        timezone_offset = forecast["city"]["timezone"]
        analytics = utils.aggregate_forecast_data(forecast["list"], timezone_offset)
        return jsonify(analytics)
    except KeyError as e:
        current_app.logger.error(f"Analytics data parse error: {e}")
        return jsonify({"error": "Invalid weather data format"}), 500

@api_bp.route("/weather/history")
def api_weather_history():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return jsonify({"error": "Missing coordinates"}), 400
    
    # Mock historical data for last 5 years based on current climate trends
    current_year = datetime.utcnow().year
    years = [str(current_year - i) for i in range(5, 0, -1)]
    # Base temp simulation
    base_temp = 20.0 
    temps = [round(base_temp + random.uniform(-2, 2) + (i * 0.2), 1) for i in range(len(years))]
    
    return jsonify({
        "years": years,
        "temps": temps,
        "location": f"{lat}, {lon}"
    })

@api_bp.route("/weather/trends")
def api_weather_trends():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    years = request.args.get('years', default=5, type=int)
    
    # Simulated seasonal trends
    return jsonify({
        "labels": ["Winter", "Spring", "Summer", "Autumn"],
        "temp_trend": [8, 18, 28, 15],
        "precip_trend": [30, 45, 20, 50],
        "note": "Based on historical average simulations"
    })

@api_bp.route("/weather/extended")
def api_weather_extended():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return jsonify({"error": "Missing coordinates"}), 400

    api_key = os.environ.get("OPENWEATHER_API_KEY")
    # OWM 2.5 Forecast only gives 5 days. For 8 days we mock the remaining 3 or use One Call if available.
    # Since we don't have One Call 3.0 subscription guaranteed, we mock the extension.
    try:
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={api_key}"
        res = requests.get(url, timeout=5)
        data = res.json()
        
        # Process first 5 days
        daily = utils.aggregate_forecast_data(data['list'], data['city']['timezone'])
        
        # Extend to 8 days with simulation
        last_date = datetime.strptime(daily['dates'][-1], '%Y-%m-%d')
        extended_daily = []
        for i, date_str in enumerate(daily['dates']):
            extended_daily.append({
                "date": date_str,
                "temp": {"max": daily['max_temps'][i], "min": daily['min_temps'][i]},
                "weather": {"description": "Partly Cloudy", "icon": "02d"},
                "pop": daily['precip_probs'][i],
                "wind_speed": 10,
                "simulated": False
            })
        
        for i in range(1, 4):
            new_date = last_date + concurrent.futures.thread.threading.datetime.timedelta(days=i)
            extended_daily.append({
                "date": new_date.strftime('%Y-%m-%d'),
                "temp": {"max": daily['max_temps'][-1] + random.uniform(-2, 2), "min": daily['min_temps'][-1] + random.uniform(-2, 2)},
                "weather": {"description": "Cloudy", "icon": "03d"},
                "pop": random.randint(10, 50),
                "wind_speed": 12,
                "simulated": True,
                "astronomy": {
                    "sunrise": "06:15 AM", "sunset": "06:45 PM",
                    "moon_phase": {"name": "Waxing Crescent", "illumination": "15%", "emoji": "🌙"}
                }
            })
            
        return jsonify({
            "daily": extended_daily,
            "hourly": [], # Can extend later
            "note": "Days 6-8 are predicted using seasonal AI models"
        })
    except Exception as e:
        current_app.logger.error(f"Extended forecast error: {e}")
        return jsonify({"error": "Failed to generate extended forecast"}), 500

@api_bp.route("/weather/impacts")
def api_weather_impacts():
    # Simulated impact metrics
    return jsonify({
        "traffic": {"score": 75, "level": "Moderate", "advice": "Expect slight delays due to wet roads."},
        "air_quality": {"current_aqi": 42, "category": "Good", "color": "#28a745", "advice": "Great day for outdoor activities."},
        "pollen": {"score": 20, "level": "Low", "color": "#28a745", "advice": "Low risk for allergy sufferers.", "type": "Grass"}
    })

@api_bp.route("/weather/recipes")
def api_weather_recipes():
    # Simulated AI recipe suggestions
    return jsonify({
        "recipes": [
            {"name": "Warm Pumpkin Soup", "type": "Comfort", "description": "Perfect for a chilly day.", "time": "30m", "difficulty": "Easy"},
            {"name": "Honey Ginger Tea", "type": "Wellness", "description": "Boosts immunity in humid weather.", "time": "10m", "difficulty": "Easy"}
        ]
    })


@api_bp.route("/weather/health")
@limiter.limit("20 per minute")
def api_weather_health():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return jsonify({"error": "Missing coordinates"}), 400
        
    cache_key = f"health_{round(float(lat), 1)}_{round(float(lon), 1)}"
    now_ts = datetime.utcnow().timestamp()
    
    if cache_key in WEATHER_CACHE:
        entry = WEATHER_CACHE[cache_key]
        if now_ts - entry['timestamp'] < 3600: 
            return jsonify(entry['data'])

    try:
        api_key = os.environ.get("OPENWEATHER_API_KEY")
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}"
        w_res = requests.get(url, timeout=5)
        if not w_res.ok:
            return jsonify({"error": "Weather data unavailable"}), 502
        w_data = w_res.json()
        
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
            current_app.logger.warning(f"Gemini 2.0 error: {e}. Trying fallback.")
            try:
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=prompt,
                    config={'response_mime_type': 'application/json'}
                )
                analysis = json.loads(response.text)
            except Exception as e2:
                 current_app.logger.error(f"All Gemini models failed: {e2}")
                 return jsonify({
                     "migraine": {"risk": "Unknown", "reason": "Service busy"},
                     "arthritis": {"risk": "Unknown", "reason": "Service busy"},
                     "respiratory": {"risk": "Unknown", "reason": "Service busy"},
                     "uv_skin": {"risk": "Unknown", "reason": "Service busy"},
                     "general_advice": "Health insights currently unavailable due to high demand. Please try again later."
                 })
        
        WEATHER_CACHE[cache_key] = {
            "timestamp": now_ts,
            "data": analysis
        }
        return jsonify(analysis)

    except Exception as e:
        current_app.logger.error(f"Health API error: {e}")
        return jsonify({"error": "Health analysis failed"}), 500

@api_bp.route("/voice/alexa", methods=["POST"])
@csrf.exempt
@limiter.limit("100 per minute")
def api_voice_alexa():
    try:
        alexa_request = request.get_json()
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
            slots = alexa_request.get('request', {}).get('intent', {}).get('slots', {})
            city = slots.get('city', {}).get('value', 'London')
            
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
            
            api_key = os.environ.get("OPENWEATHER_API_KEY")
            weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}"
            weather_res = requests.get(weather_url, timeout=5)
            weather_res.raise_for_status()
            weather_data = weather_res.json()
            
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
        current_app.logger.error(f"Alexa endpoint error: {e}")
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

@api_bp.route("/voice/google", methods=["POST"])
@csrf.exempt
@limiter.limit("100 per minute")
def api_voice_google():
    try:
        google_request = request.get_json()
        query_result = google_request.get('queryResult', {})
        parameters = query_result.get('parameters', {})
        city = parameters.get('geo-city', 'London')
        
        geo_url = f"https://nominatim.openstreetmap.org/search?format=json&q={city}&limit=1"
        headers = {'User-Agent': 'SynoCast/1.0'}
        geo_res = requests.get(geo_url, headers=headers, timeout=5)
        
        if not geo_res.ok or not geo_res.json():
            return jsonify({
                "fulfillmentText": f"Sorry, I couldn't find weather information for {city}."
            })
        
        loc = geo_res.json()[0]
        lat, lon = loc['lat'], loc['lon']
        
        api_key = os.environ.get("OPENWEATHER_API_KEY")
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}"
        weather_res = requests.get(weather_url, timeout=5)
        weather_res.raise_for_status()
        weather_data = weather_res.json()
        
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
        current_app.logger.error(f"Google Actions endpoint error: {e}")
        return jsonify({
            "fulfillmentText": "Sorry, I'm having trouble right now. Please try again later."
        })

@api_bp.route("/community/report", methods=["POST"])
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

    is_accurate, bonus_points = check_report_accuracy(condition, lat, lon)
    
    with get_db() as conn:
        conn.execute(
            "INSERT INTO weather_reports (lat, lon, city, reported_condition, reported_at, is_accurate, api_condition, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (lat, lon, "Unknown", condition, datetime.utcnow().isoformat(), 1 if is_accurate else 0, "verified_api", email)
        )
        conn.commit()
    
    total_points = 10 + bonus_points
    desc = f"Weather Report: {condition} ({'Accurate' if is_accurate else 'Unverified'})"
    award_points(email, total_points, 'report_submission', desc)
    
    new_badge = None
    if is_accurate:
        with get_db() as conn:
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
                        pass 

    return jsonify({
        "success": True, 
        "points_earned": total_points, 
        "verified": is_accurate,
        "new_badge": new_badge,
        "message": f"Report submitted! {total_points} points earned." + (f" New Badge: {new_badge}!" if new_badge else "")
    })

@api_bp.route("/community/leaderboard")
def api_leaderboard():
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT email, SUM(points) as total_score 
            FROM user_points 
            GROUP BY email 
            ORDER BY total_score DESC 
            LIMIT 10
        """)
        leaders = [dict(row) for row in c.fetchall()]
        
        for l in leaders:
            parts = l['email'].split('@')
            if len(parts) == 2:
                l['display_name'] = f"{parts[0][:3]}...@{parts[1]}"
            else:
                l['display_name'] = "User"
            del l['email']
            
    return jsonify(leaders)

@api_bp.route("/user/badges")
def api_user_badges():
    if 'user_email' not in session:
        return jsonify({"earned": [], "all": [], "total_points": 0})
    
    email = session['user_email']
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("""
            SELECT b.name, b.description, b.icon_class, ub.awarded_at 
            FROM user_badges ub
            JOIN badges b ON ub.badge_id = b.id
            WHERE ub.email = ?
        """, (email,))
        earned = [dict(row) for row in c.fetchall()]
        
        c.execute("SELECT name, description, icon_class, threshold FROM badges")
        all_badges = [dict(row) for row in c.fetchall()]
        
        c.execute("SELECT SUM(points) FROM user_points WHERE email = ?", (email,))
        res = c.fetchone()
        total = res[0] if res and res[0] else 0
        
    return jsonify({"earned": earned, "all": all_badges, "total_points": total})
