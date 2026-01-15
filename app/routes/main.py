import os
import json
from app import utils
from flask import Blueprint, render_template, jsonify, current_app, send_from_directory

main_bp = Blueprint('main', __name__)

@main_bp.context_processor
def inject_common_data():
    """Inject common data into all templates."""
    data = {
        "date_time_info": utils.get_local_time_string(),
        "global_headlines": []
    }
    
    try:
        # Fetch a few global headlines for the ticker
        news_key = os.environ.get("NEWS_API_KEY")
        if news_key:
            data["global_headlines"] = utils.fetch_weather_news(
                query="weather news headlines breaking", 
                page_size=5, 
                api_key=news_key
            )
    except Exception as e:
        current_app.logger.error(f"Error injecting global news: {e}")
        
    return data

@main_bp.route('/sw.js')
def service_worker():
    return send_from_directory(current_app.static_folder, 'sw.js', mimetype='application/javascript')

@main_bp.route('/robots.txt')
def robots_txt():
    return send_from_directory(current_app.static_folder, 'robots.txt')

@main_bp.route('/ads.txt')
def ads_txt():
    return send_from_directory(current_app.static_folder, 'ads.txt')

@main_bp.route('/sitemap.xml')
def sitemap_xml():
    return send_from_directory(current_app.static_folder, 'sitemap.xml')

@main_bp.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('logo/logo-small.svg')

@main_bp.route('/health')
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

@main_bp.route("/")
def home():
    gemini_key = os.environ.get("GEMINI_API_KEY")
    news_key = os.environ.get("NEWS_API_KEY")
    gnews_key = os.environ.get("GNEWS_API_KEY")
    
    seo_meta = {
        "description": "SynoCast provides AI-enhanced weather storytelling, hyper-local forecasts, and curated weather news using Gemini AI.",
        "keywords": "weather, AI weather, weather news, local forecast, SynoCast, climate events, severe weather alerts"
    }
    
    # Latest Headlines - Specifcally Pakistan Weather via GNews
    raw_latest = utils.fetch_gnews_weather(query="Pakistan weather", page_size=10, api_key=gnews_key)
    if not raw_latest:
        raw_latest = utils.fetch_weather_news(query="weather news headlines breaking", page_size=10, api_key=news_key)
        
    latest_news = utils.categorize_news_with_ai(raw_latest, gemini_key)
    
    # Around The World news
    raw_world = utils.fetch_weather_news(query="global weather news headlines", page_size=10, api_key=news_key)
    world_news = utils.categorize_news_with_ai(raw_world, gemini_key)
    
    return render_template(
        "home.html", 
        active_page="home", 
        latest_news=latest_news,
        world_news=world_news,
        meta=seo_meta
    )

@main_bp.route("/news")
def news():
    gemini_key = os.environ.get("GEMINI_API_KEY")
    news_key = os.environ.get("NEWS_API_KEY")
    gnews_key = os.environ.get("GNEWS_API_KEY")
    
    seo_meta = {
        "description": "Stay updated with SynoCast's AI-curated weather headlines, breaking alerts, and featured climate stories from around the globe.",
        "keywords": "breaking news, weather alerts, climate change stories, storm warnings, weather news today"
    }
    
    raw_news = utils.fetch_gnews_weather(query="Pakistan weather", page_size=15, api_key=gnews_key)
    if not raw_news or (raw_news and raw_news[0].get('source', {}).get('name') == 'SynoNews'):
         raw_news = utils.fetch_weather_news(query="weather news headlines breaking global", page_size=20, api_key=news_key)
    
    all_categorized = utils.categorize_news_with_ai(raw_news, gemini_key)
    
    breaking_news = [a for a in all_categorized if a.get('urgency') in ['Critical', 'High']]
    featured_news = [a for a in all_categorized if a.get('category') in ['Climate Events', 'Weather Impact News', 'Hydrological Updates']]
    
    if not breaking_news: breaking_news = all_categorized[:4]
    if not featured_news: featured_news = all_categorized[4:8]

    return render_template(
        "news.html", 
        active_page="news", 
        breaking_news=breaking_news,
        featured_news=featured_news,
        meta=seo_meta
    )

@main_bp.route("/travel")
def travel():
    seo_meta = {
        "description": "Plan your trip with SynoCast's Travel Dashboard. Features weather forecasts, currency conversion, and packing list suggestions.",
        "keywords": "travel weather, trip planner, currency converter, packing list, historical weather"
    }
    return render_template("travel.html", active_page="travel", meta=seo_meta)

@main_bp.route("/terms")
def terms():
    return render_template("terms.html", active_page="terms")

@main_bp.route("/map")
def map_explorer():
    seo_meta = {
        "description": "Explore global weather patterns with SynoCast's immersive 3D map. View wind, rain, temperature, and cloud layers in real-time.",
        "keywords": "weather map, 3D globe, wind map, rain radar, temperature heatmap, global weather"
    }
    return render_template("map.html", active_page="map", meta=seo_meta)

@main_bp.route("/learn")
def weather_wisdom():
    seo_meta = {
        "description": "Master weather concepts with SynoCast's Weather Wisdom. Learn about climate science, terminology, and daily trivia.",
        "keywords": "weather education, climate change explainers, weather glossary, meteorology for beginners, weather trivia"
    }
    return render_template("learn.html", active_page="learn", meta=seo_meta)

@main_bp.route("/compare")
def compare_cities():
    seo_meta = {
        "description": "Compare weather conditions between two cities side-by-side. Analyze temperature, humidity, and pollution differences.",
        "keywords": "weather comparison, city vs city, climate comparison, weather battle, temperature comparison"
    }
    return render_template("compare.html", active_page="compare", meta=seo_meta)

@main_bp.route("/weather")
def weather():
    dt_info = utils.get_local_time_string()
    gemini_key = os.environ.get("GEMINI_API_KEY")
    news_key = os.environ.get("NEWS_API_KEY")
    
    seo_meta = {
        "description": "Get detailed local weather forecasts, interactive maps, and AI-driven weather insights with SynoCast.",
        "keywords": "local weather, hourly forecast, weather map, AI weather recommendations, humidity, wind speed"
    }
    
    raw_weather = utils.fetch_weather_news(query="local weather forecast updates", country=dt_info.get('country'), page_size=10, api_key=news_key)
    weather_news = utils.categorize_news_with_ai(raw_weather, gemini_key)
    
    return render_template(
        "weather.html", 
        active_page="weather", 
        weather_news=weather_news,
        meta=seo_meta
    )

@main_bp.route("/subscribe")
def subscribe():
    seo_meta = {
        "description": "Subscribe to SynoCast for hyper-local weather alerts and daily AI weather news delivered directly to your inbox.",
        "keywords": "subscribe, weather alerts, email notifications, SynoCast subscription"
    }
    return render_template("subscribe.html", active_page="subscribe", meta=seo_meta)

@main_bp.route("/about")
def about():
    seo_meta = {
        "description": "Learn more about SynoCast, our mission to provide AI-enhanced weather storytelling, and how we use technology to keep you ahead of the storm.",
        "keywords": "about SynoCast, weather company, AI weather technology, mission"
    }
    return render_template("about.html", active_page="about", meta=seo_meta)

@main_bp.route("/offline")
def offline():
    return render_template("offline.html", active_page="offline")

@main_bp.route('/pakistan')
def pakistan():
    try:
        cities_path = os.path.join(current_app.static_folder, 'pakistan_cities.json')
        with open(cities_path, 'r', encoding='utf-8') as f:
            cities = json.load(f)
        
        seo_meta = {
            "description": "Real-time weather updates and forecasts for major cities across Pakistan.",
            "keywords": "Pakistan weather, Karachi weather, Lahore weather, Islamabad, forecast"
        }
        
        return render_template(
            "pakistan.html", 
            active_page="pakistan", 
            cities_json=json.dumps(cities), 
            meta=seo_meta
        )
    except Exception as e:
        current_app.logger.error(f"Pakistan page error: {e}")
        return render_template("500.html"), 500

