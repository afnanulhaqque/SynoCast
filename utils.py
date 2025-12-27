import os
import requests
import logging
import json
import google.generativeai as genai
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
        genai.configure(api_key=api_key)
        # Use the latest flash model for categorization
        model = genai.GenerativeModel("gemini-flash-latest")


        
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

        response = model.generate_content(prompt)
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
