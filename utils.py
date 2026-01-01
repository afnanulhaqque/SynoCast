import os
import requests
import logging
import json
import time
import math
import random
from google import genai
from datetime import datetime, timedelta, timezone
from flask import request, session

NEWS_CACHE = {}
AI_NEWS_CACHE = {}
NEWS_CACHE_DURATION = 3600
AI_CACHE_DURATION = 300 # 5 minutes for AI categorization


logger = logging.getLogger(__name__)

def get_client_ip():
    """Get user IP address, handling proxies."""
    return request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0]

def get_local_time_string():
    ip = get_client_ip()
    
    if "location_data" in session and session["location_data"].get("ip") == ip:
        data = session["location_data"]
        city = data.get("city", "Unknown")
        region = data.get("region", "")
        country = data.get("country", "Pakistan")
        country_code = data.get("country_code", "PK")
        utc_offset = data.get("utc_offset", "+0500")
    else:
        if ip.startswith("127.") or ip == "localhost" or ip == "::1":
            city, region, country, country_code, utc_offset = "Islamabad", "Punjab", "Pakistan", "PK", "+0500"
            session["location_data"] = {
                "ip": ip, 
                "city": city, 
                "region": region, 
                "country": country,
                "country_code": country_code,
                "utc_offset": utc_offset
            }
        else:
            try:
                resp = requests.get(f"https://ipapi.co/{ip}/json/", timeout=2)
                resp.raise_for_status()
                data = resp.json()
                city = data.get("city", "Unknown")
                region = data.get("region", "")
                country = data.get("country_name", "Unknown")
                country_code = data.get("country_code", "")
                utc_offset = data.get("utc_offset", "+0000")
                session["location_data"] = {
                    "ip": ip, 
                    "city": city, 
                    "region": region, 
                    "country": country,
                    "country_code": country_code,
                    "utc_offset": utc_offset
                }
            except Exception:
                city, region, country, country_code, utc_offset = "Unknown", "", "Unknown", "", "+0000"

    try:
        offset_hours = int(utc_offset[:3])
        offset_minutes = int(utc_offset[3:])
    except (ValueError, TypeError):
        offset_hours = offset_minutes = 0

    tz = timezone(timedelta(hours=offset_hours, minutes=offset_minutes))
    now = datetime.now(tz)
    formatted = now.strftime("%A, %B %d, %Y, %H:%M")
    gmt_offset = f"GMT{utc_offset[:3]}:{utc_offset[3:]}"
    full_string = f"{formatted} Time zone in {city} - {region} ({gmt_offset})"

    return {
        "display_string": full_string,
        "city": city,
        "region": region,
        "country": country,
        "country_code": country_code,
        "utc_offset": utc_offset,
        "gmt_label": gmt_offset
    }

def get_dummy_news():
    """Helper to return high-quality dummy weather news when API fails."""
    return [
        {
            "title": "Severe Storm Warning Issued for Midwestern Regions",
            "description": "Met agencies have issued critical alerts as a major storm system moves across the Midwest, bringing potential floods and high winds.",
            "url": "#",
            "urlToImage": "https://images.unsplash.com/photo-1527482797697-8795b05a13fe?q=80&w=1000&auto=format&fit=crop",
            "publishedAt": datetime.now().isoformat(),
            "source": {"name": "SynoNews"}
        },
        {
            "title": "Global Climate Summit Highlights Rising Ocean Temperatures",
            "description": "Scientists at the recent global summit expressed urgent concerns over the rapid increase in sea surface temperatures this year.",
            "url": "#",
            "urlToImage": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?q=80&w=1000&auto=format&fit=crop",
            "publishedAt": datetime.now().isoformat(),
            "source": {"name": "ClimateWatch"}
        },
        {
            "title": "Air Quality Index Reaches Hazardous Levels in Major Metro Areas",
            "description": "A combination of stagnant air and regional wildfires has pushed the AQI into the red zone, prompting health advisories.",
            "url": "#",
            "urlToImage": "https://images.unsplash.com/photo-1590602847861-f357a9332bbc?q=80&w=1000&auto=format&fit=crop",
            "publishedAt": datetime.now().isoformat(),
            "source": {"name": "Health First"}
        },
        {
            "title": "New Study Reveals Accelerated Melting of Arctic Sea Ice",
            "description": "Researchers warn that the Arctic could see ice-free summers much sooner than previously predicted, with serious global implications.",
            "url": "#",
            "urlToImage": "https://images.unsplash.com/photo-1581093196277-9f60807dbf06?q=80&w=1000&auto=format&fit=crop",
            "publishedAt": datetime.now().isoformat(),
            "source": {"name": "EcoToday"}
        },
        {
            "title": "Monsoon Rainfall Patterns Shifting Due to Climate Variability",
            "description": "Recent data suggests that the intensity and timing of monsoons are changing, affecting agriculture in several South Asian countries.",
            "url": "#",
            "urlToImage": "https://images.unsplash.com/photo-1534274988757-a28bf1f53ee1?q=80&w=1000&auto=format&fit=crop",
            "publishedAt": datetime.now().isoformat(),
            "source": {"name": "WorldWeather"}
        }
    ]

def fetch_weather_news(query="weather", country=None, page_size=10, api_key=None):
    if not api_key:
        return get_dummy_news()
        
    cache_key = f"{query}_{country}_{page_size}"
    if cache_key in NEWS_CACHE:
        cached = NEWS_CACHE[cache_key]
        if datetime.now().timestamp() - cached["timestamp"] < NEWS_CACHE_DURATION:
            return cached["articles"]

    try:
        # Refine query: Just use the query + weather keywords
        # If query already has 'weather', don't repeat it too much
        # Refined keywords integrated from test_news_api.py
        essential_weather = "(weather OR climate OR storm OR forecast OR temperature OR rainfall OR snowfall OR earthquake OR flood OR drought OR hurricane OR cyclone OR typhoon OR wildfire OR heatwave OR coldwave OR meteorology OR blizzard OR tornado)"
        
        # NewsAPI 'everything' endpoint accepts Boolean operators
        if query and "weather" not in query.lower():
            q = f"({query}) AND ({essential_weather})"
        else:
            q = query if query else essential_weather
            
        params = {
            "q": q,
            "pageSize": page_size * 2, # Fetch more to allow for filtering
            "apiKey": api_key,
            "language": "en",
            "sortBy": "relevance"
        }
        
        response = requests.get("https://newsapi.org/v2/everything", params=params, timeout=10)
        
        if response.status_code in [429, 426]:
             logger.warning(f"NewsAPI Limit Hit ({response.status_code}). Using dummy data.")
             return get_dummy_news()
             
        if response.status_code in [401, 403]:
             logger.error(f"NewsAPI Auth Error ({response.status_code}). Check API Key.")
             return get_dummy_news()
             
        if not response.ok:
            logger.error(f"NewsAPI error: {response.status_code} - {response.text}")
            return []
            
        articles = [a for a in response.json().get("articles", []) 
                    if a.get("title") and a.get("title") != "[Removed]"]
        
        # Secondary local filter: less strict to avoid empty results
        weather_terms = ['weather', 'forecast', 'storm', 'rain', 'snow', 'temp', 'climate', 'flood', 
                         'drought', 'heat', 'cold', 'wind', 'degree', 'celsius', 'fahrenheit', 
                         'monsoon', 'cyclone', 'typhoon', 'hurricane', 'blizzard', 'meteorology']
        
        filtered_articles = []
        for a in articles:
            text = (a.get('title', '') + ' ' + (a.get('description') or '')).lower()
            if any(term in text for term in weather_terms):
                filtered_articles.append(a)
            elif len(filtered_articles) < 3: # Keep a few even if terms don't match exactly to avoid empty UI
                filtered_articles.append(a)

        # Ensure we return at most page_size
        results = filtered_articles[:page_size]

        # ULTIMATE FALLBACK: If no news found even after multiple attempts, use dummy news
        if not results:
            logger.info("No weather results found from API. Using dummy news.")
            return get_dummy_news()

        NEWS_CACHE[cache_key] = {
            "timestamp": datetime.now().timestamp(),
            "articles": results
        }
        return results
    except Exception as e:
        logger.error(f"News fetch error: {e}")
        return []

def fetch_gnews_weather(query="weather", page_size=10, api_key=None):
    """
    Fetch weather news using GNews API.
    Used specifically for Pakistan weather news as per user request.
    """
    if not api_key:
        logger.warning("No GNews API key provided.")
        return get_dummy_news()

    cache_key = f"gnews_{query}_{page_size}"
    if cache_key in NEWS_CACHE:
        cached = NEWS_CACHE[cache_key]
        if datetime.now().timestamp() - cached["timestamp"] < NEWS_CACHE_DURATION:
            return cached["articles"]

    try:
        # GNews endpoint
        url = "https://gnews.io/api/v4/search"
        
        # Construct query: ensure 'Pakistan' and 'weather' are prioritized
        # The user specifically requested "Pakistani Weather news"
        if "pakistan" not in query.lower():
            q = f"{query} AND Pakistan"
        else:
            q = query
            
        params = {
            "q": q,
            "lang": "en",
            "max": page_size,
            "apikey": api_key,
            "country": "pk" # Prioritize Pakistan
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if not response.ok:
            logger.error(f"GNews API error: {response.status_code} - {response.text}")
            return get_dummy_news()
            
        data = response.json()
        raw_articles = data.get("articles", [])
        
        formatted_articles = []
        for a in raw_articles:
            formatted_articles.append({
                "title": a.get("title"),
                "description": a.get("description"),
                "url": a.get("url"),
                "urlToImage": a.get("image"), # GNews uses 'image' instead of 'urlToImage'
                "publishedAt": a.get("publishedAt"),
                "source": {"name": a.get("source", {}).get("name")},
                "location": "Pakistan", # Explicitly set for Pakistan news
                "urgency": "Medium" # Default urgency
            })
            
        # Cache results
        NEWS_CACHE[cache_key] = {
            "timestamp": datetime.now().timestamp(),
            "articles": formatted_articles
        }
        
        if not formatted_articles:
             return get_dummy_news()
             
        return formatted_articles

    except Exception as e:
        logger.error(f"GNews fetch error: {e}")
        return get_dummy_news()


def categorize_news_with_ai(articles, api_key):
    """
    Uses Gemini to filter for weather-only content and categorize articles.
    Returns fallback results if no API key is provided.
    """
    if not articles:
        return []

    # Simple caching logic: use titles to detect if we've seen this exact bundle
    titles_hash = hash(tuple(a.get('title', '') for a in articles[:15]))
    now_ts = datetime.now().timestamp()
    
    if titles_hash in AI_NEWS_CACHE:
        cached = AI_NEWS_CACHE[titles_hash]
        if now_ts - cached["timestamp"] < AI_CACHE_DURATION:
            logger.info("Serving categorized news from AI cache")
            return cached["data"]

    if not api_key:

        # Fallback filter for news without AI
        weather_terms = ['weather', 'forecast', 'storm', 'rain', 'snow', 'temp', 'climate', 'flood', 
                         'drought', 'heat', 'cold', 'wind', 'degree', 'celsius', 'fahrenheit', 'monsoon', 'cyclone']
        
        fallback_results = []
        for a in articles:
            text = (a.get('title', '') + ' ' + a.get('description', '')).lower()
            if not any(term in text for term in weather_terms):
                continue

            pub_date = a.get("publishedAt") or datetime.now().isoformat()
            fallback_results.append({
                "category": "Weather News",
                "title": a.get("title") or "Weather Update",
                "summary": (a.get("description")[:200] + "...") if a.get("description") else "No summary available.",
                "urgency": "Medium",
                "location": "Global",
                "url": a.get("url") or "#",
                "urlToImage": a.get("urlToImage"),
                "publishedAt": str(pub_date)
            })
        return fallback_results

    try:
        client = genai.Client(api_key=api_key)

        
        article_summaries = []
        for a in articles[:15]: # Limit to first 15 to stay within tokens and time
            article_summaries.append({
                "title": a.get("title"),
                "description": a.get("description"),
                "url": a.get("url"),
                "urlToImage": a.get("urlToImage"),
                "publishedAt": a.get("publishedAt"),
                "source": a.get("source", {}).get("name")
            })

        categories = [
            "Severe Weather Alerts",
            "Climate Events",
            "Air Quality and Heat Index Reports",
            "Weather Impact News",
            "Hydrological Updates"
        ]

        prompt = f"""
        You are a strict weather news filter. Analyze the following news articles. 
        Discard ANY article that is not explicitly about:
        - Weather phenomena (rain, snow, wind, storms, etc.)
        - Climate change or global warming
        - Natural disasters (floods, droughts, earthquakes, wildfires)
        - Meteorological forecasts or reports
        - Environmental climate impact
        
        If an article is about politics, entertainment, general technology, or sports (unless directly weather-impacted), DISCARD it.
        
        Categorize the remaining articles into ONE of these categories: {', '.join(categories)}.
        
        For each valid weather article, provide:
        - category: One of the five categories listed above.
        - title: The original headline.
        - summary: A 2-3 sentence engaging summary.
        - urgency: One of [Critical, High, Medium, Low].
        - location: The primary geographic area affected (City, Country, or Region).
        - url: The original URL.
        - urlToImage: The original image URL.
        - publishedAt: The original timestamp.
        
        Return the result as a STRICT JSON list of objects. Do not include any other text.
        
        Articles:
        {json.dumps(article_summaries)}
        """

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt
        )
        content = response.text.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()

        categorized_articles = json.loads(content)
        results = []
        if isinstance(categorized_articles, list):
            results = categorized_articles
        elif isinstance(categorized_articles, dict) and "articles" in categorized_articles:
            results = categorized_articles["articles"]
        
        if results:
            AI_NEWS_CACHE[titles_hash] = {
                "timestamp": now_ts,
                "data": results
            }
            return results
        
        raise ValueError("AI response is not a valid list")

    except Exception as e:
        logger.error(f"AI categorization error: {e}")
        # Fallback: if AI fails, just return a simplified version of the first few articles
        # with a generic category
        fallback_results = []
        for a in (articles or [])[:8]:
            pub_date = a.get("publishedAt")
            if not pub_date:
                pub_date = datetime.now().isoformat()
            
            fallback_results.append({
                "category": "Weather News",
                "title": a.get("title") or "Weather Update",
                "summary": (a.get("description")[:200] + "...") if a.get("description") else "Check the full story for more details.",
                "urgency": "Medium",
                "location": "Global",
                "url": a.get("url") or "#",
                "urlToImage": a.get("urlToImage"),
                "publishedAt": str(pub_date)
            })
        return fallback_results

def aggregate_forecast_data(forecast_list, timezone_offset=0):
    """
    Aggregates 3-hourly forecast data into daily summaries for analytics.
    Returns lists suitable for Chart.js.
    """
    daily_data = {}
    
    for item in forecast_list:
        # Adjust for local time
        dt_utc = datetime.fromtimestamp(item['dt'], tz=timezone.utc)
        dt_local = dt_utc + timedelta(seconds=timezone_offset)
        date_str = dt_local.strftime('%Y-%m-%d')
        
        if date_str not in daily_data:
            daily_data[date_str] = {
                'min_temp': item['main']['temp_min'],
                'max_temp': item['main']['temp_max'],
                'pop': item.get('pop', 0),
                'rain': item.get('rain', {}).get('3h', 0),
                'date_obj': dt_local
            }
        else:
            daily_data[date_str]['min_temp'] = min(daily_data[date_str]['min_temp'], item['main']['temp_min'])
            daily_data[date_str]['max_temp'] = max(daily_data[date_str]['max_temp'], item['main']['temp_max'])
            daily_data[date_str]['pop'] = max(daily_data[date_str]['pop'], item.get('pop', 0))
            daily_data[date_str]['rain'] += item.get('rain', {}).get('3h', 0)

    # Sort by date
    sorted_dates = sorted(daily_data.keys())
    
    # Format output lists
    display_dates = [daily_data[d]['date_obj'].strftime('%a %d') for d in sorted_dates]
    min_temps = [round(daily_data[d]['min_temp'], 1) for d in sorted_dates]
    max_temps = [round(daily_data[d]['max_temp'], 1) for d in sorted_dates]
    precip_probs = [round(daily_data[d]['pop'] * 100) for d in sorted_dates]
    rain_totals = [round(daily_data[d]['rain'], 1) for d in sorted_dates]
    
    return {
        "dates": display_dates,
        "min_temps": min_temps,
        "max_temps": max_temps,
        "precip_probs": precip_probs,
        "rain_totals": rain_totals
    }

def calculate_golden_hours(sunrise_ts, sunset_ts, timezone_offset=0):
    """
    Calculate golden hour windows for photographers.
    Golden hour is approximately 1 hour after sunrise and 1 hour before sunset.
    
    Args:
        sunrise_ts: Unix timestamp of sunrise
        sunset_ts: Unix timestamp of sunset
        timezone_offset: Timezone offset in seconds
    
    Returns:
        dict with morning and evening golden hour start/end times
    """
    try:
        # Adjust for timezone
        sunrise_local = datetime.fromtimestamp(sunrise_ts, tz=timezone.utc) + timedelta(seconds=timezone_offset)
        sunset_local = datetime.fromtimestamp(sunset_ts, tz=timezone.utc) + timedelta(seconds=timezone_offset)
        
        # Morning golden hour: sunrise to sunrise + 1 hour
        morning_start = sunrise_local
        morning_end = sunrise_local + timedelta(hours=1)
        
        # Evening golden hour: sunset - 1 hour to sunset
        evening_start = sunset_local - timedelta(hours=1)
        evening_end = sunset_local
        
        return {
            "morning": {
                "start": morning_start.strftime("%H:%M"),
                "end": morning_end.strftime("%H:%M"),
                "start_ts": int(morning_start.timestamp()),
                "end_ts": int(morning_end.timestamp())
            },
            "evening": {
                "start": evening_start.strftime("%H:%M"),
                "end": evening_end.strftime("%H:%M"),
                "start_ts": int(evening_start.timestamp()),
                "end_ts": int(evening_end.timestamp())
            }
        }
    except Exception as e:
        logger.error(f"Golden hour calculation error: {e}")
        return None

def interpret_moon_phase(phase_decimal):
    """
    Convert moon phase decimal (0-1) to readable format with emoji.
    
    Moon phase values:
    - 0 and 1: New Moon
    - 0.25: First Quarter
    - 0.5: Full Moon
    - 0.75: Last Quarter
    
    Args:
        phase_decimal: Moon phase value from 0 to 1
    
    Returns:
        dict with phase name, emoji, and description
    """
    try:
        phase = float(phase_decimal)
        
        if phase == 0 or phase == 1:
            return {"name": "New Moon", "emoji": "🌑", "illumination": "0%"}
        elif 0 < phase < 0.25:
            return {"name": "Waxing Crescent", "emoji": "🌒", "illumination": f"{int(phase * 100)}%"}
        elif phase == 0.25:
            return {"name": "First Quarter", "emoji": "🌓", "illumination": "50%"}
        elif 0.25 < phase < 0.5:
            return {"name": "Waxing Gibbous", "emoji": "🌔", "illumination": f"{int(phase * 100)}%"}
        elif phase == 0.5:
            return {"name": "Full Moon", "emoji": "🌕", "illumination": "100%"}
        elif 0.5 < phase < 0.75:
            return {"name": "Waning Gibbous", "emoji": "🌖", "illumination": f"{int((1 - phase) * 100)}%"}
        elif phase == 0.75:
            return {"name": "Last Quarter", "emoji": "🌗", "illumination": "50%"}
        else:  # 0.75 < phase < 1
            return {"name": "Waning Crescent", "emoji": "🌘", "illumination": f"{int((1 - phase) * 100)}%"}
    except Exception as e:
        logger.error(f"Moon phase interpretation error: {e}")
        return {"name": "Unknown", "emoji": "🌑", "illumination": "N/A"}

def format_astronomy_data(daily_item, timezone_offset=0):
    """
    Format astronomy data from One Call API daily forecast.
    
    Args:
        daily_item: Single day item from One Call API daily forecast
        timezone_offset: Timezone offset in seconds
    
    Returns:
        dict with formatted sunrise, sunset, moonrise, moonset, moon phase, and golden hours
    """
    try:
        sunrise_ts = daily_item.get('sunrise')
        sunset_ts = daily_item.get('sunset')
        moonrise_ts = daily_item.get('moonrise')
        moonset_ts = daily_item.get('moonset')
        moon_phase = daily_item.get('moon_phase', 0)
        
        # Format times
        def format_time(ts):
            if ts:
                dt = datetime.fromtimestamp(ts, tz=timezone.utc) + timedelta(seconds=timezone_offset)
                return dt.strftime("%H:%M")
            return "N/A"
        
        result = {
            "sunrise": format_time(sunrise_ts),
            "sunset": format_time(sunset_ts),
            "moonrise": format_time(moonrise_ts),
            "moonset": format_time(moonset_ts),
            "moon_phase": interpret_moon_phase(moon_phase),
            "sunrise_ts": sunrise_ts,
            "sunset_ts": sunset_ts
        }
        
        # Calculate golden hours
        if sunrise_ts and sunset_ts:
            golden_hours = calculate_golden_hours(sunrise_ts, sunset_ts, timezone_offset)
            if golden_hours:
                result["golden_hours"] = golden_hours
        
        return result
    except Exception as e:
        logger.error(f"Astronomy data formatting error: {e}")
        return None

# ============================================================================
# HISTORICAL WEATHER DATA & CLIMATE TRENDS
# ============================================================================

HISTORICAL_CACHE = {}
HISTORICAL_CACHE_DURATION = 86400  # 24 hours for historical data

def fetch_historical_weather(lat, lon, date):
    """
    Fetch historical weather data from Open-Meteo Archive API.
    
    Args:
        lat: Latitude
        lon: Longitude
        date: datetime object or string in 'YYYY-MM-DD' format
    
    Returns:
        dict with historical weather data or None on error
    """
    try:
        # Convert date to string if datetime object
        if isinstance(date, datetime):
            date_str = date.strftime('%Y-%m-%d')
        else:
            date_str = date
        
        # Check cache
        cache_key = f"hist_{lat}_{lon}_{date_str}"
        now_ts = datetime.now().timestamp()
        
        if cache_key in HISTORICAL_CACHE:
            cached = HISTORICAL_CACHE[cache_key]
            if now_ts - cached["timestamp"] < HISTORICAL_CACHE_DURATION:
                logger.info(f"Serving historical data for {date_str} from cache")
                return cached["data"]
        
        # Open-Meteo Archive API (free, no API key required)
        url = f"https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": date_str,
            "end_date": date_str,
            "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,windspeed_10m_max,weathercode",
            "timezone": "auto"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract daily data
        if data.get('daily') and len(data['daily'].get('time', [])) > 0:
            result = {
                "date": data['daily']['time'][0],
                "temp_max": data['daily']['temperature_2m_max'][0],
                "temp_min": data['daily']['temperature_2m_min'][0],
                "temp_mean": data['daily']['temperature_2m_mean'][0],
                "precipitation": data['daily']['precipitation_sum'][0],
                "wind_speed": data['daily']['windspeed_10m_max'][0],
                "weather_code": data['daily']['weathercode'][0],
                "source": "Open-Meteo Archive"
            }
            
            # Cache the result
            HISTORICAL_CACHE[cache_key] = {
                "timestamp": now_ts,
                "data": result
            }
            
            return result
        
        return None
        
    except Exception as e:
        logger.error(f"Historical weather fetch error: {e}")
        return None

def fetch_climate_normals(lat, lon, month):
    """
    Fetch climate normals (30-year averages) for a location and month.
    Uses Open-Meteo Climate API for global coverage.
    
    Args:
        lat: Latitude
        lon: Longitude
        month: Month number (1-12)
    
    Returns:
        dict with climate normals or None on error
    """
    try:
        # Check cache
        cache_key = f"normals_{lat}_{lon}_{month}"
        now_ts = datetime.now().timestamp()
        
        if cache_key in HISTORICAL_CACHE:
            cached = HISTORICAL_CACHE[cache_key]
            if now_ts - cached["timestamp"] < HISTORICAL_CACHE_DURATION * 7:  # Cache for 7 days
                return cached["data"]
        
        # Open-Meteo Climate API
        # Get the current year's data for the specific month to calculate normals
        current_year = datetime.now().year
        start_date = f"{current_year - 30}-{month:02d}-01"
        end_date = f"{current_year}-{month:02d}-28"  # Safe end date for all months
        
        url = f"https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "auto"
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.ok:
            data = response.json()
            
            # Calculate averages
            if data.get('daily'):
                temps_max = [t for t in data['daily']['temperature_2m_max'] if t is not None]
                temps_min = [t for t in data['daily']['temperature_2m_min'] if t is not None]
                precip = [p for p in data['daily']['precipitation_sum'] if p is not None]
                
                result = {
                    "month": month,
                    "temp_max_avg": sum(temps_max) / len(temps_max) if temps_max else None,
                    "temp_min_avg": sum(temps_min) / len(temps_min) if temps_min else None,
                    "temp_mean_avg": (sum(temps_max) + sum(temps_min)) / (len(temps_max) + len(temps_min)) if temps_max and temps_min else None,
                    "precipitation_avg": sum(precip) / len(precip) if precip else None,
                    "source": "Open-Meteo Climate (30-year estimate)"
                }
                
                # Cache the result
                HISTORICAL_CACHE[cache_key] = {
                    "timestamp": now_ts,
                    "data": result
                }
                
                return result
        
        # Fallback: Use simplified estimates based on latitude
        # This is a rough approximation for demo purposes
        logger.warning(f"Climate normals API failed, using latitude-based estimates")
        
        # Simplified temperature estimates based on latitude
        lat_abs = abs(lat)
        if lat_abs < 23.5:  # Tropics
            base_temp = 27
        elif lat_abs < 40:  # Subtropics
            base_temp = 20
        elif lat_abs < 60:  # Temperate
            base_temp = 12
        else:  # Polar
            base_temp = 0
        
        # Add seasonal variation
        if month in [12, 1, 2]:  # Winter
            seasonal_adj = -5 if lat > 0 else 5
        elif month in [6, 7, 8]:  # Summer
            seasonal_adj = 5 if lat > 0 else -5
        else:  # Spring/Fall
            seasonal_adj = 0
        
        result = {
            "month": month,
            "temp_max_avg": base_temp + seasonal_adj + 5,
            "temp_min_avg": base_temp + seasonal_adj - 5,
            "temp_mean_avg": base_temp + seasonal_adj,
            "precipitation_avg": 50,  # Generic estimate
            "source": "Estimated (latitude-based)"
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Climate normals fetch error: {e}")
        return None

def calculate_climate_anomaly(current_temp, normal_temp):
    """
    Calculate temperature anomaly (deviation from normal).
    
    Args:
        current_temp: Current temperature
        normal_temp: Normal (average) temperature
    
    Returns:
        dict with anomaly value and interpretation
    """
    try:
        if current_temp is None or normal_temp is None:
            return None
        
        anomaly = current_temp - normal_temp
        
        # Interpret the anomaly
        if abs(anomaly) < 1:
            category = "normal"
            description = "Near average"
        elif abs(anomaly) < 3:
            category = "slightly_abnormal"
            description = "Slightly warmer" if anomaly > 0 else "Slightly cooler"
        elif abs(anomaly) < 5:
            category = "abnormal"
            description = "Warmer" if anomaly > 0 else "Cooler"
        else:
            category = "very_abnormal"
            description = "Much warmer" if anomaly > 0 else "Much cooler"
        
        return {
            "anomaly": round(anomaly, 1),
            "category": category,
            "description": description,
            "direction": "warmer" if anomaly > 0 else "cooler" if anomaly < 0 else "normal"
        }
        
    except Exception as e:
        logger.error(f"Climate anomaly calculation error: {e}")
        return None

def analyze_seasonal_trends(lat, lon, years_back=5):
    """
    Analyze seasonal temperature and precipitation trends over multiple years.
    
    Args:
        lat: Latitude
        lon: Longitude
        years_back: Number of years to analyze (default 5)
    
    Returns:
        dict with seasonal trend data
    """
    try:
        current_year = datetime.now().year
        start_year = current_year - years_back
        
        # Fetch data for each year
        yearly_data = []
        
        for year in range(start_year, current_year):
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"
            
            url = f"https://archive-api.open-meteo.com/v1/archive"
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": start_date,
                "end_date": end_date,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                "timezone": "auto"
            }
            
            try:
                response = requests.get(url, params=params, timeout=10)
                if response.ok:
                    data = response.json()
                    yearly_data.append({
                        "year": year,
                        "data": data.get('daily', {})
                    })
            except:
                continue
        
        if not yearly_data:
            return None
        
        # Analyze trends by season
        seasons = {
            "winter": [12, 1, 2],
            "spring": [3, 4, 5],
            "summer": [6, 7, 8],
            "fall": [9, 10, 11]
        }
        
        seasonal_trends = {}
        
        for season_name, months in seasons.items():
            season_temps = []
            season_precip = []
            
            for year_data in yearly_data:
                year = year_data["year"]
                daily = year_data["data"]
                
                if not daily.get('time'):
                    continue
                
                # Extract data for this season
                for i, date_str in enumerate(daily['time']):
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    if date_obj.month in months:
                        if daily.get('temperature_2m_max') and i < len(daily['temperature_2m_max']):
                            temp_max = daily['temperature_2m_max'][i]
                            temp_min = daily['temperature_2m_min'][i]
                            if temp_max is not None and temp_min is not None:
                                season_temps.append((temp_max + temp_min) / 2)
                        
                        if daily.get('precipitation_sum') and i < len(daily['precipitation_sum']):
                            precip = daily['precipitation_sum'][i]
                            if precip is not None:
                                season_precip.append(precip)
            
            if season_temps:
                seasonal_trends[season_name] = {
                    "avg_temp": round(sum(season_temps) / len(season_temps), 1),
                    "total_precip": round(sum(season_precip), 1) if season_precip else 0,
                    "data_points": len(season_temps)
                }
        
        return {
            "years_analyzed": years_back,
            "seasons": seasonal_trends,
            "source": "Open-Meteo Archive"
        }
        
    except Exception as e:
        logger.error(f"Seasonal trends analysis error: {e}")
        return None

def get_record_temperatures(lat, lon, years_back=10):
    """
    Track record high and low temperatures from historical data.
    
    Args:
        lat: Latitude
        lon: Longitude
        years_back: Number of years to search (default 10)
    
    Returns:
        dict with record temperatures and dates
    """
    try:
        current_year = datetime.now().year
        start_year = current_year - years_back
        
        start_date = f"{start_year}-01-01"
        end_date = f"{current_year - 1}-12-31"
        
        url = f"https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_max,temperature_2m_min",
            "timezone": "auto"
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if not response.ok:
            return None
        
        data = response.json()
        daily = data.get('daily', {})
        
        if not daily.get('time'):
            return None
        
        # Find records
        record_high = {"temp": float('-inf'), "date": None}
        record_low = {"temp": float('inf'), "date": None}
        
        for i, date_str in enumerate(daily['time']):
            temp_max = daily['temperature_2m_max'][i]
            temp_min = daily['temperature_2m_min'][i]
            
            if temp_max is not None and temp_max > record_high["temp"]:
                record_high = {"temp": temp_max, "date": date_str}
            
            if temp_min is not None and temp_min < record_low["temp"]:
                record_low = {"temp": temp_min, "date": date_str}
        
        return {
            "record_high": {
                "temperature": round(record_high["temp"], 1),
                "date": record_high["date"],
                "year": int(record_high["date"][:4]) if record_high["date"] else None
            },
            "record_low": {
                "temperature": round(record_low["temp"], 1),
                "date": record_low["date"],
                "year": int(record_low["date"][:4]) if record_low["date"] else None
            },
            "years_analyzed": years_back,
            "source": "Open-Meteo Archive"
        }
        
    except Exception as e:
        logger.error(f"Record temperatures fetch error: {e}")
        return None

# ============================================================================
# AI Outfit Suggestion Functions
# ============================================================================

def get_outfit_suggestion(temperature, condition, precipitation_prob=0, activity="casual", wind_speed=0):
    """
    Get outfit suggestions based on weather conditions.
    
    Args:
        temperature: Temperature in Celsius
        condition: Weather condition string (e.g., 'Clear', 'Rain', 'Snow')
        precipitation_prob: Probability of precipitation (0-100)
        activity: Activity type ('casual', 'work', 'outdoor', 'formal')
        wind_speed: Wind speed in m/s
    
    Returns:
        Dict with outfit description, items, and image prompt
    """
    condition_lower = condition.lower()
    outfit = {
        "items": [],
        "accessories": [],
        "footwear": "",
        "description": "",
        "image_prompt": ""
    }
    
    # Base clothing by temperature
    if temperature < 0:
        outfit["items"] = ["Heavy winter coat", "Thermal layers", "Thick sweater", "Warm pants"]
        outfit["footwear"] = "Insulated winter boots"
        outfit["accessories"] = ["Warm hat", "Scarf", "Gloves"]
        temp_desc = "freezing cold"
    elif temperature < 10:
        outfit["items"] = ["Winter jacket", "Long-sleeve shirt", "Sweater", "Jeans or warm pants"]
        outfit["footwear"] = "Closed-toe shoes or boots"
        outfit["accessories"] = ["Light scarf", "Beanie"]
        temp_desc = "cold"
    elif temperature < 15:
        outfit["items"] = ["Light jacket or cardigan", "Long-sleeve shirt", "Jeans"]
        outfit["footwear"] = "Sneakers or casual shoes"
        outfit["accessories"] = ["Light jacket"]
        temp_desc = "cool"
    elif temperature < 20:
        outfit["items"] = ["Light sweater or hoodie", "T-shirt", "Jeans or casual pants"]
        outfit["footwear"] = "Sneakers"
        outfit["accessories"] = []
        temp_desc = "mild"
    elif temperature < 25:
        outfit["items"] = ["T-shirt or blouse", "Light pants or jeans"]
        outfit["footwear"] = "Sneakers or loafers"
        outfit["accessories"] = ["Sunglasses"]
        temp_desc = "pleasant"
    elif temperature < 30:
        outfit["items"] = ["Light t-shirt", "Shorts or light pants"]
        outfit["footwear"] = "Sandals or breathable sneakers"
        outfit["accessories"] = ["Sunglasses", "Sun hat"]
        temp_desc = "warm"
    else:
        outfit["items"] = ["Breathable light clothing", "Shorts", "Tank top or light t-shirt"]
        outfit["footwear"] = "Sandals or flip-flops"
        outfit["accessories"] = ["Sunglasses", "Wide-brim hat", "Sunscreen"]
        temp_desc = "hot"
    
    # Weather condition adjustments
    if 'rain' in condition_lower or 'drizzle' in condition_lower or precipitation_prob > 50:
        outfit["accessories"].extend(["Umbrella", "Waterproof jacket"])
        outfit["footwear"] = "Waterproof boots or shoes"
        weather_desc = "rainy"
    elif 'snow' in condition_lower:
        outfit["accessories"].extend(["Waterproof gloves", "Snow boots"])
        outfit["footwear"] = "Insulated snow boots"
        weather_desc = "snowy"
    elif 'cloud' in condition_lower:
        weather_desc = "cloudy"
    elif 'clear' in condition_lower or 'sun' in condition_lower:
        weather_desc = "sunny"
        if temperature > 20:
            outfit["accessories"].append("Sunscreen")
    else:
        weather_desc = condition_lower
    
    # Wind adjustments
    if wind_speed > 10:
        outfit["accessories"].append("Windbreaker")
    
    # Activity-based adjustments
    if activity == "work" or activity == "formal":
        outfit["items"] = [item.replace("T-shirt", "Dress shirt").replace("Jeans", "Dress pants") 
                          for item in outfit["items"]]
        outfit["footwear"] = outfit["footwear"].replace("Sneakers", "Dress shoes")
        activity_desc = "professional"
    elif activity == "outdoor":
        outfit["items"].append("Athletic wear")
        outfit["footwear"] = "Hiking boots or athletic shoes"
        outfit["accessories"].append("Backpack")
        activity_desc = "outdoor adventure"
    else:
        activity_desc = "casual"
    
    # Generate description
    outfit["description"] = (
        f"For this {temp_desc} and {weather_desc} weather ({temperature}°C), "
        f"we recommend {activity_desc} attire. "
        f"Layer with {', '.join(outfit['items'][:2])} and wear {outfit['footwear']}. "
    )
    
    if outfit["accessories"]:
        outfit["description"] += f"Don't forget: {', '.join(outfit['accessories'])}."
    
    # Generate image prompt for AI
    outfit["image_prompt"] = (
        f"A stylish {activity_desc} outfit laid out on a clean surface, "
        f"featuring {', '.join(outfit['items'][:3])}, {outfit['footwear']}, "
        f"and {', '.join(outfit['accessories'][:2]) if outfit['accessories'] else 'minimal accessories'}. "
        f"Modern fashion photography, {weather_desc} weather theme, professional lighting, "
        f"flat lay composition, high quality, detailed textures"
    )
    
    return outfit



def get_exchange_rates(api_key=None, base_currency="USD"):
    """
    Fetch and cache currency exchange rates.
    Updates once every 24 hours.
    """
    from app import get_db
    import sqlite3
    
    # Try fetching from cache first
    try:
        with get_db() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT rate, target_currency FROM currency_rates WHERE base_currency = ? AND last_updated > ?", 
                      (base_currency, (datetime.now() - timedelta(hours=24)).isoformat()))
            cached_rows = c.fetchall()
            cached_rates = {row['target_currency']: row['rate'] for row in cached_rows}
            
            if cached_rates:
                return cached_rates
    except Exception as e:
        logger.error(f"Error fetching cached rates: {e}")

    # Fallback to API if cache is stale or empty
    # Default rates if no API key
    default_rates = {
        "USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 150.25, "CNY": 7.21, 
        "PKR": 278.50, "INR": 82.95, "AUD": 1.53, "CAD": 1.35
    }
    
    if not api_key:
        return default_rates
        
    try:
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}"
        res = requests.get(url, timeout=10)
        if res.ok:
            data = res.json()
            rates = data.get('conversion_rates', {})
            
            # Save to cache
            with get_db() as conn:
                for target, rate in rates.items():
                    conn.execute("""
                        INSERT OR REPLACE INTO currency_rates (base_currency, target_currency, rate, last_updated)
                        VALUES (?, ?, ?, ?)
                    """, (base_currency, target, rate, datetime.now().isoformat()))
                conn.commit()
            
            return rates
    except Exception as e:
        logger.error(f"Error fetching exchange rates from API: {e}")
        
    return default_rates

def convert_currency(amount, from_curr, to_curr, rates=None):
    """Convert amount from one currency to another."""
    if from_curr == to_curr:
        return amount
        
    if not rates:
        rates = get_exchange_rates()
        
    # If rates are base=USD, we need to convert to USD first if from_curr is not USD
    if from_curr != "USD":
        from_rate = rates.get(from_curr, 1)
        amount_usd = amount / from_rate if from_rate else amount
    else:
        amount_usd = amount
        
    to_rate = rates.get(to_curr, 1)
    return amount_usd * to_rate

def get_travel_cost_insights(lat, lon, currency_pref="USD"):
    """
    Calculate weather-based travel costs for a location.
    Provides estimates for seasonal items based on current weather.
    """
    base_prices = {
        "umbrella": 15.0,
        "sunscreen": 12.0,
        "winter_jacket": 80.0,
        "cold_drink": 3.0,
        "hot_coffee": 4.0
    }
    
    rates = get_exchange_rates()
    converted_prices = {item: round(convert_currency(price, "USD", currency_pref, rates), 2) 
                        for item, price in base_prices.items()}
    
    return converted_prices

def calculate_traffic_impact(weather_data, temperature):
    """
    Calculate traffic impact based on weather conditions.
    
    Args:
        weather_data: Dict containing weather condition info
        temperature: Current temperature in Celsius
    
    Returns:
        Dict with traffic impact score (1-10), description, and advice
    """
    condition = weather_data.get('main', 'Clear').lower()
    description = weather_data.get('description', '').lower()
    
    # Base impact score
    impact_score = 1
    impact_level = "Minimal"
    advice = "Normal traffic conditions expected."
    
    # Weather condition impacts
    if 'thunderstorm' in condition or 'thunderstorm' in description:
        impact_score = 9
        impact_level = "Severe"
        advice = "Heavy delays expected. Avoid travel if possible. Allow extra 40-60 minutes."
    elif 'snow' in condition or 'snow' in description:
        if 'heavy' in description:
            impact_score = 10
            impact_level = "Extreme"
            advice = "Roads may be impassable. Avoid all non-essential travel."
        else:
            impact_score = 7
            impact_level = "High"
            advice = "Significant delays likely. Drive carefully and allow extra 30-45 minutes."
    elif 'rain' in condition or 'rain' in description:
        if 'heavy' in description or 'extreme' in description:
            impact_score = 8
            impact_level = "Very High"
            advice = "Major delays expected. Allow extra 35-50 minutes for your commute."
        elif 'moderate' in description:
            impact_score = 5
            impact_level = "Moderate"
            advice = "Moderate delays possible. Allow extra 15-20 minutes."
        else:
            impact_score = 3
            impact_level = "Low"
            advice = "Minor delays possible. Allow extra 5-10 minutes."
    elif 'fog' in condition or 'mist' in condition or 'fog' in description:
        impact_score = 6
        impact_level = "Moderate-High"
        advice = "Reduced visibility. Drive slowly and allow extra 20-30 minutes."
    elif 'wind' in description or condition == 'squall':
        impact_score = 4
        impact_level = "Low-Moderate"
        advice = "Strong winds may affect high-profile vehicles. Allow extra 10-15 minutes."
    
    # Temperature adjustments
    if temperature < -10:
        impact_score = min(10, impact_score + 2)
        advice += " Icy conditions likely."
    elif temperature > 35:
        impact_score = min(10, impact_score + 1)
        advice += " Heat may affect vehicle performance."
    
    return {
        "score": impact_score,
        "level": impact_level,
        "advice": advice,
        "icon": get_traffic_icon(impact_score)
    }


def calculate_air_quality_prediction(weather_data, temperature, humidity, wind_speed, current_aqi=None):
    """
    Predict air quality trends based on weather conditions.
    
    Args:
        weather_data: Dict containing weather condition info
        temperature: Temperature in Celsius
        humidity: Humidity percentage
        wind_speed: Wind speed in m/s
        current_aqi: Current AQI value (optional)
    
    Returns:
        Dict with AQI prediction, trend, and health advice
    """
    condition = weather_data.get('main', 'Clear').lower()
    
    # Base AQI (if not provided, estimate based on conditions)
    if current_aqi is None:
        current_aqi = 50  # Default moderate value
    
    # Calculate trend modifiers
    trend_modifier = 0
    
    # Wind disperses pollutants
    if wind_speed > 5:
        trend_modifier -= 15
        trend_direction = "improving"
    elif wind_speed < 2:
        trend_modifier += 10
        trend_direction = "worsening"
    else:
        trend_direction = "stable"
    
    # Rain clears air
    if 'rain' in condition:
        trend_modifier -= 20
        trend_direction = "improving significantly"
    
    # High humidity can trap pollutants
    if humidity > 80 and wind_speed < 3:
        trend_modifier += 10
    
    # Temperature inversions (cold air trapped under warm)
    if temperature < 5 and wind_speed < 2:
        trend_modifier += 15
        trend_direction = "worsening"
    
    # High temperatures can increase ground-level ozone
    if temperature > 30:
        trend_modifier += 10
    
    # Calculate predicted AQI
    predicted_aqi = max(0, min(500, current_aqi + trend_modifier))
    
    # Determine category and advice
    if predicted_aqi <= 50:
        category = "Good"
        advice = "Air quality is excellent. Perfect for outdoor activities!"
        color = "#00e400"
    elif predicted_aqi <= 100:
        category = "Moderate"
        advice = "Air quality is acceptable. Sensitive individuals should limit prolonged outdoor exertion."
        color = "#ffff00"
    elif predicted_aqi <= 150:
        category = "Unhealthy for Sensitive Groups"
        advice = "People with respiratory conditions should reduce outdoor activities."
        color = "#ff7e00"
    elif predicted_aqi <= 200:
        category = "Unhealthy"
        advice = "Everyone should reduce prolonged outdoor exertion."
        color = "#ff0000"
    elif predicted_aqi <= 300:
        category = "Very Unhealthy"
        advice = "Avoid outdoor activities. Health alert for everyone."
        color = "#8f3f97"
    else:
        category = "Hazardous"
        advice = "Stay indoors. Emergency conditions for all."
        color = "#7e0023"
    
    return {
        "current_aqi": current_aqi,
        "predicted_aqi": round(predicted_aqi),
        "trend": trend_direction,
        "category": category,
        "advice": advice,
        "color": color
    }


def calculate_pollen_count(temperature, humidity, wind_speed, weather_condition, month=None):
    """
    Estimate pollen count based on weather conditions.
    
    Args:
        temperature: Temperature in Celsius
        humidity: Humidity percentage
        wind_speed: Wind speed in m/s
        weather_condition: Main weather condition
        month: Current month (1-12), defaults to current month
    
    Returns:
        Dict with pollen level, count estimate, and advice
    """
    if month is None:
        month = datetime.now().month
    
    # Base pollen count
    pollen_score = 0
    
    # Seasonal factors (Northern Hemisphere)
    if month in [3, 4, 5]:  # Spring - Tree pollen
        pollen_score = 7
        pollen_type = "tree pollen"
    elif month in [6, 7, 8]:  # Summer - Grass pollen
        pollen_score = 6
        pollen_type = "grass pollen"
    elif month in [9, 10]:  # Fall - Ragweed
        pollen_score = 5
        pollen_type = "ragweed"
    else:  # Winter - Low pollen
        pollen_score = 1
        pollen_type = "general allergens"
    
    # Temperature effects (optimal pollen release: 15-25Â°C)
    if 15 <= temperature <= 25:
        pollen_score += 2
    elif temperature < 10 or temperature > 30:
        pollen_score -= 2
    
    # Humidity effects (high humidity reduces airborne pollen)
    if humidity > 70:
        pollen_score -= 2
    elif humidity < 40:
        pollen_score += 1
    
    # Wind effects (moderate wind spreads pollen)
    if 2 <= wind_speed <= 5:
        pollen_score += 2
    elif wind_speed > 8:
        pollen_score -= 1
    
    # Weather condition effects
    condition_lower = weather_condition.lower()
    if 'rain' in condition_lower:
        pollen_score -= 3  # Rain washes away pollen
    elif 'clear' in condition_lower or 'sun' in condition_lower:
        pollen_score += 1
    
    # Normalize score
    pollen_score = max(0, min(10, pollen_score))
    
    # Determine level and advice
    if pollen_score <= 2:
        level = "Low"
        advice = "Great day for allergy sufferers! Minimal pollen in the air."
        color = "#00e400"
    elif pollen_score <= 4:
        level = "Low-Moderate"
        advice = "Pollen levels are manageable. Sensitive individuals may experience mild symptoms."
        color = "#92d050"
    elif pollen_score <= 6:
        level = "Moderate"
        advice = "Moderate pollen levels. Consider taking allergy medication if needed."
        color = "#ffff00"
    elif pollen_score <= 8:
        level = "High"
        advice = "High pollen count. Allergy sufferers should take precautions and limit outdoor time."
        color = "#ff7e00"
    else:
        level = "Very High"
        advice = "Very high pollen levels. Keep windows closed and avoid outdoor activities if allergic."
        color = "#ff0000"
    
    return {
        "score": pollen_score,
        "level": level,
        "type": pollen_type,
        "advice": advice,
        "color": color
    }


def get_traffic_icon(score):
    """Get appropriate icon for traffic impact score."""
    if score >= 8:
        return "fa-circle-exclamation"
    elif score >= 5:
        return "fa-triangle-exclamation"
    elif score >= 3:
        return "fa-circle-info"
    else:
        return "fa-circle-check"


def get_all_impacts(weather_data, temperature, humidity, wind_speed, current_aqi=None):
    """
    Get all impact predictions in a single call.
    
    Args:
        weather_data: Dict containing weather condition info
        temperature: Temperature in Celsius
        humidity: Humidity percentage
        wind_speed: Wind speed in m/s
        current_aqi: Current AQI value (optional)
    
    Returns:
        Dict with traffic, air_quality, and pollen predictions
    """
    return {
        "traffic": calculate_traffic_impact(weather_data, temperature),
        "air_quality": calculate_air_quality_prediction(
            weather_data, temperature, humidity, wind_speed, current_aqi
        ),
        "pollen": calculate_pollen_count(
            temperature, humidity, wind_speed, weather_data.get('main', 'Clear')
        )
    }
# Recipe database categorized by weather conditions
RECIPE_DATABASE = {
    "cold": [
        {
            "name": "Classic Chicken Noodle Soup",
            "description": "Warm, comforting soup perfect for cold weather. A timeless remedy for chilly days.",
            "prep_time": "45 min",
            "servings": 6,
            "difficulty": "Easy",
            "ingredients": ["chicken", "noodles", "carrots", "celery", "onion", "chicken broth"],
            "meal_type": ["lunch", "dinner"],
            "image_prompt": "A steaming bowl of chicken noodle soup with vegetables, warm lighting, cozy atmosphere"
        },
        {
            "name": "Beef Stew with Root Vegetables",
            "description": "Hearty and filling stew that warms you from the inside out.",
            "prep_time": "2 hours",
            "servings": 8,
            "difficulty": "Medium",
            "ingredients": ["beef", "potatoes", "carrots", "onions", "beef broth", "herbs"],
            "meal_type": ["dinner"],
            "image_prompt": "Rich beef stew in a rustic bowl with chunks of vegetables, steam rising"
        },
        {
            "name": "Hot Chocolate with Marshmallows",
            "description": "Rich, creamy hot chocolate topped with fluffy marshmallows.",
            "prep_time": "10 min",
            "servings": 2,
            "difficulty": "Easy",
            "ingredients": ["milk", "cocoa powder", "sugar", "marshmallows", "vanilla"],
            "meal_type": ["snack", "breakfast"],
            "image_prompt": "Mug of hot chocolate with marshmallows, whipped cream, cozy winter setting"
        },
        {
            "name": "Baked Mac and Cheese",
            "description": "Creamy, cheesy comfort food with a crispy golden top.",
            "prep_time": "40 min",
            "servings": 6,
            "difficulty": "Easy",
            "ingredients": ["pasta", "cheddar cheese", "milk", "butter", "breadcrumbs"],
            "meal_type": ["lunch", "dinner"],
            "image_prompt": "Baked mac and cheese with golden crispy top, cheese bubbling, comfort food"
        },
        {
            "name": "Chili Con Carne",
            "description": "Spicy, warming chili packed with beans and ground beef.",
            "prep_time": "1 hour",
            "servings": 8,
            "difficulty": "Easy",
            "ingredients": ["ground beef", "kidney beans", "tomatoes", "chili peppers", "onions"],
            "meal_type": ["lunch", "dinner"],
            "image_prompt": "Bowl of spicy chili con carne with beans, topped with cheese and sour cream"
        }
    ],
    "hot": [
        {
            "name": "Greek Salad with Grilled Chicken",
            "description": "Light, refreshing salad perfect for hot summer days.",
            "prep_time": "20 min",
            "servings": 4,
            "difficulty": "Easy",
            "ingredients": ["lettuce", "tomatoes", "cucumber", "feta cheese", "olives", "chicken"],
            "meal_type": ["lunch", "dinner"],
            "image_prompt": "Fresh Greek salad with grilled chicken, colorful vegetables, bright summer lighting"
        },
        {
            "name": "Watermelon Mint Cooler",
            "description": "Refreshing drink to beat the heat. Hydrating and delicious.",
            "prep_time": "10 min",
            "servings": 4,
            "difficulty": "Easy",
            "ingredients": ["watermelon", "mint", "lime", "ice", "honey"],
            "meal_type": ["snack", "breakfast"],
            "image_prompt": "Glass of watermelon mint cooler with ice, fresh mint leaves, summer vibes"
        },
        {
            "name": "Gazpacho (Cold Tomato Soup)",
            "description": "Chilled Spanish soup bursting with fresh vegetable flavors.",
            "prep_time": "15 min + chill time",
            "servings": 6,
            "difficulty": "Easy",
            "ingredients": ["tomatoes", "cucumber", "bell peppers", "onion", "garlic", "olive oil"],
            "meal_type": ["lunch", "snack"],
            "image_prompt": "Bowl of cold gazpacho soup, vibrant red color, garnished with vegetables"
        },
        {
            "name": "Caprese Salad",
            "description": "Simple Italian salad with fresh mozzarella, tomatoes, and basil.",
            "prep_time": "10 min",
            "servings": 4,
            "difficulty": "Easy",
            "ingredients": ["mozzarella", "tomatoes", "basil", "olive oil", "balsamic vinegar"],
            "meal_type": ["lunch", "snack"],
            "image_prompt": "Caprese salad with fresh mozzarella and tomatoes, drizzled with balsamic glaze"
        },
        {
            "name": "Grilled Fish Tacos",
            "description": "Light and flavorful tacos with grilled fish and fresh toppings.",
            "prep_time": "30 min",
            "servings": 4,
            "difficulty": "Medium",
            "ingredients": ["white fish", "tortillas", "cabbage", "lime", "avocado", "cilantro"],
            "meal_type": ["lunch", "dinner"],
            "image_prompt": "Grilled fish tacos with fresh toppings, colorful presentation, summer meal"
        }
    ],
    "rainy": [
        {
            "name": "Tomato Basil Soup with Grilled Cheese",
            "description": "Classic comfort combo perfect for rainy days.",
            "prep_time": "30 min",
            "servings": 4,
            "difficulty": "Easy",
            "ingredients": ["tomatoes", "basil", "cream", "bread", "cheese", "butter"],
            "meal_type": ["lunch", "dinner"],
            "image_prompt": "Tomato soup in a bowl with grilled cheese sandwich, rainy day comfort food"
        },
        {
            "name": "Creamy Mushroom Risotto",
            "description": "Rich, creamy risotto that's perfect for cozy indoor dining.",
            "prep_time": "45 min",
            "servings": 4,
            "difficulty": "Medium",
            "ingredients": ["arborio rice", "mushrooms", "parmesan", "white wine", "butter", "broth"],
            "meal_type": ["dinner"],
            "image_prompt": "Creamy mushroom risotto in a bowl, garnished with parmesan, elegant presentation"
        },
        {
            "name": "Chai Tea Latte",
            "description": "Spiced tea latte to warm you up on a rainy afternoon.",
            "prep_time": "15 min",
            "servings": 2,
            "difficulty": "Easy",
            "ingredients": ["black tea", "milk", "cinnamon", "ginger", "cardamom", "honey"],
            "meal_type": ["snack", "breakfast"],
            "image_prompt": "Chai tea latte in a mug with cinnamon stick, cozy rainy day setting"
        },
        {
            "name": "Chicken Pot Pie",
            "description": "Flaky pastry filled with creamy chicken and vegetables.",
            "prep_time": "1 hour",
            "servings": 6,
            "difficulty": "Medium",
            "ingredients": ["chicken", "puff pastry", "carrots", "peas", "cream", "potatoes"],
            "meal_type": ["dinner"],
            "image_prompt": "Golden chicken pot pie with flaky crust, steam escaping, comfort food"
        }
    ],
    "mild": [
        {
            "name": "Quinoa Buddha Bowl",
            "description": "Nutritious bowl packed with colorful vegetables and protein.",
            "prep_time": "30 min",
            "servings": 2,
            "difficulty": "Easy",
            "ingredients": ["quinoa", "chickpeas", "avocado", "sweet potato", "kale", "tahini"],
            "meal_type": ["lunch", "dinner"],
            "image_prompt": "Colorful Buddha bowl with quinoa and vegetables, healthy and vibrant"
        },
        {
            "name": "Margherita Pizza",
            "description": "Classic pizza with fresh mozzarella, tomatoes, and basil.",
            "prep_time": "45 min",
            "servings": 4,
            "difficulty": "Medium",
            "ingredients": ["pizza dough", "mozzarella", "tomatoes", "basil", "olive oil"],
            "meal_type": ["lunch", "dinner"],
            "image_prompt": "Margherita pizza fresh from the oven, melted cheese, fresh basil leaves"
        },
        {
            "name": "Chicken Caesar Wrap",
            "description": "Portable and delicious wrap perfect for outdoor activities.",
            "prep_time": "15 min",
            "servings": 2,
            "difficulty": "Easy",
            "ingredients": ["tortilla", "chicken", "romaine lettuce", "caesar dressing", "parmesan"],
            "meal_type": ["lunch"],
            "image_prompt": "Chicken caesar wrap cut in half, showing fresh ingredients, casual meal"
        },
        {
            "name": "Pasta Primavera",
            "description": "Light pasta dish with seasonal vegetables.",
            "prep_time": "25 min",
            "servings": 4,
            "difficulty": "Easy",
            "ingredients": ["pasta", "zucchini", "bell peppers", "cherry tomatoes", "garlic", "olive oil"],
            "meal_type": ["lunch", "dinner"],
            "image_prompt": "Pasta primavera with colorful vegetables, light and fresh, spring meal"
        }
    ]
}


def get_weather_category(temperature, condition):
    """
    Categorize weather into recipe-friendly categories.
    
    Args:
        temperature: Temperature in Celsius
        condition: Weather condition string
    
    Returns:
        String category: 'cold', 'hot', 'rainy', or 'mild'
    """
    condition_lower = condition.lower()
    
    # Rain takes precedence
    if 'rain' in condition_lower or 'drizzle' in condition_lower or 'shower' in condition_lower:
        return "rainy"
    
    # Temperature-based categories
    if temperature < 10:
        return "cold"
    elif temperature > 28:
        return "hot"
    else:
        return "mild"


def get_recipe_suggestions(temperature, condition, meal_type=None, count=3):
    """
    Get recipe suggestions based on weather conditions.
    
    Args:
        temperature: Temperature in Celsius
        condition: Weather condition string
        meal_type: Optional filter for meal type ('breakfast', 'lunch', 'dinner', 'snack')
        count: Number of recipes to return (default 3)
    
    Returns:
        List of recipe dictionaries with weather context
    """
    category = get_weather_category(temperature, condition)
    recipes = RECIPE_DATABASE.get(category, RECIPE_DATABASE["mild"])
    
    # Filter by meal type if specified
    if meal_type:
        filtered_recipes = [r for r in recipes if meal_type.lower() in r["meal_type"]]
        if filtered_recipes:
            recipes = filtered_recipes
    
    # Randomly select recipes
    selected_recipes = random.sample(recipes, min(count, len(recipes)))
    
    # Add weather context to each recipe
    weather_context = get_weather_context(temperature, condition, category)
    
    for recipe in selected_recipes:
        recipe["weather_context"] = weather_context
        recipe["weather_category"] = category
    
    return selected_recipes


def get_weather_context(temperature, condition, category):
    """
    Generate contextual message explaining why these recipes fit the weather.
    
    Args:
        temperature: Temperature in Celsius
        condition: Weather condition string
        category: Weather category
    
    Returns:
        String with weather context
    """
    contexts = {
        "cold": f"It's a chilly {temperature}Â°C outside. Warm up with these comforting dishes!",
        "hot": f"Beat the {temperature}Â°C heat with these refreshing, light meals!",
        "rainy": f"Perfect weather for cozy comfort food. Stay dry and enjoy!",
        "mild": f"Beautiful {temperature}Â°C weather! These balanced meals are perfect for today."
    }
    
    return contexts.get(category, "Enjoy these delicious recipes!")


def get_seasonal_recipes(month=None):
    """
    Get recipes appropriate for the current season.
    
    Args:
        month: Month number (1-12), defaults to current month
    
    Returns:
        List of seasonal recipe suggestions
    """
    if month is None:
        month = datetime.now().month
    
    # Determine season (Northern Hemisphere)
    if month in [12, 1, 2]:
        season = "winter"
        return RECIPE_DATABASE["cold"]
    elif month in [3, 4, 5]:
        season = "spring"
        return RECIPE_DATABASE["mild"]
    elif month in [6, 7, 8]:
        season = "summer"
        return RECIPE_DATABASE["hot"]
    else:  # 9, 10, 11
        season = "fall"
        return RECIPE_DATABASE["mild"] + RECIPE_DATABASE["rainy"][:2]


def format_recipe_for_display(recipe):
    """
    Format recipe data for frontend display.
    
    Args:
        recipe: Recipe dictionary
    
    Returns:
        Formatted recipe dictionary
    """
    return {
        "name": recipe["name"],
        "description": recipe["description"],
        "prepTime": recipe["prep_time"],
        "servings": recipe["servings"],
        "difficulty": recipe["difficulty"],
        "ingredients": recipe["ingredients"],
        "mealType": recipe["meal_type"],
        "weatherContext": recipe.get("weather_context", ""),
        "imagePrompt": recipe.get("image_prompt", "")
    }
