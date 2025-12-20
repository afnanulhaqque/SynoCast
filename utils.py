import os
import requests
import logging
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
        utc_offset = data.get("utc_offset", "+0000")
    else:
        if ip.startswith("127.") or ip == "localhost" or ip == "::1":
            city, region, utc_offset = "Islamabad", "Punjab", "+0500"
            session["location_data"] = {"ip": ip, "city": city, "region": region, "utc_offset": utc_offset}
        else:
            try:
                resp = requests.get(f"https://ipapi.co/{ip}/json/", timeout=2)
                resp.raise_for_status()
                data = resp.json()
                city = data.get("city", "Unknown")
                region = data.get("region", "")
                utc_offset = data.get("utc_offset", "+0000")
                session["location_data"] = {"ip": ip, "city": city, "region": region, "utc_offset": utc_offset}
            except Exception:
                city, region, utc_offset = "Unknown", "", "+0000"

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
        "utc_offset": utc_offset,
        "gmt_label": gmt_offset
    }

def fetch_weather_news(query="weather", country=None, page_size=10, api_key=None):
    if not api_key:
        return []
        
    cache_key = f"{query}_{country}_{page_size}"
    if cache_key in NEWS_CACHE:
        cached = NEWS_CACHE[cache_key]
        if datetime.now().timestamp() - cached["timestamp"] < NEWS_CACHE_DURATION:
            return cached["articles"]

    try:
        params = {
            "q": f"{query} {country}" if country else query,
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
