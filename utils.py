import os
import requests
import logging
import json
import google.generativeai as genai
from datetime import datetime, timedelta, timezone
from flask import request, session

NEWS_CACHE = {}
NEWS_CACHE_DURATION = 3600

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

def fetch_weather_news(query="weather", country=None, page_size=10, api_key=None):
    if not api_key:
        # Provide high-quality sample data if API key is missing so user can see the UI
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
            }
        ]
        
    cache_key = f"{query}_{country}_{page_size}"
    if cache_key in NEWS_CACHE:
        cached = NEWS_CACHE[cache_key]
        if datetime.now().timestamp() - cached["timestamp"] < NEWS_CACHE_DURATION:
            return cached["articles"]

    try:
        params = {
            "q": f"{query} {country}" if country and country.lower() != "unknown" else query,
            "pageSize": page_size,
            "apiKey": api_key,
            "language": "en",
            "sortBy": "publishedAt"
        }
        
        response = requests.get("https://newsapi.org/v2/everything", params=params, timeout=10)
        if not response.ok:
            return []
            
        articles = [a for a in response.json().get("articles", []) 
                    if a.get("title") and a.get("title") != "[Removed]"]
        
        NEWS_CACHE[cache_key] = {
            "timestamp": datetime.now().timestamp(),
            "articles": articles
        }
        return articles
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

    if not api_key:
        # Fallback format for news without AI categorization
        fallback_results = []
        for a in articles:
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
        # Use a faster/newer model for categorization
        model = genai.GenerativeModel("gemini-1.5-flash")
        
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
        Analyze the following news articles and Filter out ANY that are NOT strictly weather-related.
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
        if isinstance(categorized_articles, list):
            return categorized_articles
        elif isinstance(categorized_articles, dict) and "articles" in categorized_articles:
            return categorized_articles["articles"]
        
        raise ValueError("AI response is not a list")
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
