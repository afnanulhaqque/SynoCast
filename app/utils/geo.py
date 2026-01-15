import requests
import logging
from datetime import datetime, timedelta, timezone
from flask import request, session

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
