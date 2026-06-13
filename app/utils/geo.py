import os
import re
import requests
import logging
from datetime import datetime, timedelta, timezone
from flask import request, session

logger = logging.getLogger(__name__)

def clean_urdu_text(text):
    if not text:
        return text
    
    # Common replacements for locations in Pakistan to keep it natural and correct
    replacements = {
        "اسلام آباد": "Islamabad",
        "راولپنڈی": "Rawalpindi",
        "کراچی": "Karachi",
        "لاہور": "Lahore",
        "پشاور": "Peshawar",
        "کوئٹہ": "Quetta",
        "ملتان": "Multan",
        "فیصل آباد": "Faisalabad",
        "سیالکوٹ": "Sialkot",
        "گوجرانوالہ": "Gujranwala",
        "حیدرآباد": "Hyderabad",
        "سکردو": "Skardu",
        "گلگت": "Gilgit",
        "مظفر آباد": "Muzaffarabad",
        "کشمیر": "Kashmir",
        "پاکستان": "Pakistan",
        "پنجاب": "Punjab",
        "سندھ": "Sindh",
        "خیبر پختونخوا": "Khyber Pakhtunkhwa",
        "بلوچستان": "Balochistan",
        "وفاقی دارالحکومت": "Federal Capital Territory",
        "آئی-10": "I-10",
        "آئی-11": "I-11",
        "آئی-12": "I-12",
        "آئی-8": "I-8",
        "آئی-9": "I-9",
        "ایچ-8": "H-8",
        "ایچ-9": "H-9",
        "ایچ-10": "H-10",
        "ایچ-11": "H-11",
        "جی-6": "G-6",
        "جی-7": "G-7",
        "جی-8": "G-8",
        "جی-9": "G-9",
        "جی-10": "G-10",
        "جی-11": "G-11",
        "جی-13": "G-13",
        "جی-15": "G-15",
        "جی-12": "G-12",
        "جی-14": "G-14",
        "ایف-6": "F-6",
        "ایف-7": "F-7",
        "ایف-8": "F-8",
        "ایف-9": "F-9",
        "ایف-10": "F-10",
        "ایف-11": "F-11",
        "ایف-15": "F-15",
        "ای-7": "E-7",
        "ای-8": "E-8",
        "ای-9": "E-9",
        "ای-11": "E-11",
        "ڈی-12": "D-12",
        "ڈی-17": "D-17",
        "ڈی-18": "D-18",
        "سی-15": "C-15",
        "سی-16": "C-16",
        "بی-17": "B-17",
        "گلی": "Gali",
        "سڑک": "Road",
        "چوک": "Chowk",
        "مارکیٹ": "Market",
        "سیکٹر": "Sector"
    }
    
    for urdu, eng in replacements.items():
        text = text.replace(urdu, eng)
        
    # Check if still contains Urdu/Arabic characters
    if re.search(r'[\u0600-\u06FF]', text):
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            try:
                from google import genai
                client = genai.Client(api_key=gemini_key.strip())
                prompt = f"Translate the following location/address string to English. Return ONLY the English translation without quotes or explanations: '{text}'"
                response = client.models.generate_content(
                    model="gemini-2.0-flash-exp",
                    contents=prompt
                )
                translated = response.text.strip()
                if translated and not re.search(r'[\u0600-\u06FF]', translated):
                    return translated
            except Exception:
                pass
                
        # Fallback: remove any Arabic characters
        text = re.sub(r'[\u0600-\u06FF]', '', text).strip()
        # Clean up multiple spaces or trailing commas
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r',\s*,', ',', text).strip(' ,')
        
    return text

def clean_dict_values(data):
    if isinstance(data, dict):
        return {k: clean_dict_values(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_dict_values(x) for x in data]
    elif isinstance(data, str):
        return clean_urdu_text(data)
    else:
        return data

def get_client_ip():
    """Get user IP address, handling proxies."""
    return request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0]

def get_local_time_string():
    ip = get_client_ip()
    
    if "location_data" in session and session["location_data"].get("ip") == ip:
        data = session["location_data"]
        city = clean_urdu_text(data.get("city", "Unknown"))
        region = clean_urdu_text(data.get("region", ""))
        country = clean_urdu_text(data.get("country", "Pakistan"))
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
                city = clean_urdu_text(data.get("city", "Unknown"))
                region = clean_urdu_text(data.get("region", ""))
                country = clean_urdu_text(data.get("country_name", "Unknown"))
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

def translate_to_urdu(text):
    if not text:
        return text
        
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key.strip())
            prompt = (
                f"Translate the following English or mixed location/address string to Urdu script. "
                f"Ensure it is natural, correct, and in Urdu script. "
                f"Return ONLY the Urdu translation, without quotes, prefix, suffix, or explanation. "
                f"Input: '{text}'"
            )
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt
            )
            translated = response.text.strip()
            if translated:
                return translated
        except Exception as e:
            logger.error(f"Gemini Urdu Translation Error: {e}")

    # Fallback dictionary for basic translation
    replacements = {
        "Islamabad": "اسلام آباد",
        "Rawalpindi": "راولپنڈی",
        "Karachi": "کراچی",
        "Lahore": "لاہور",
        "Peshawar": "پشاور",
        "Quetta": "کوئٹہ",
        "Multan": "ملتان",
        "Faisalabad": "فیصل آباد",
        "Sialkot": "سیالکوٹ",
        "Gujranwala": "گوجرانوالہ",
        "Hyderabad": "حیدرآباد",
        "Skardu": "سکردو",
        "Gilgit": "گلگت",
        "Muzaffarabad": "مظفر آباد",
        "Kashmir": "کشمیر",
        "Pakistan": "پاکستان",
        "Punjab": "پنجاب",
        "Sindh": "سندھ",
        "Khyber Pakhtunkhwa": "خیبر پختونخوا",
        "Balochistan": "بلوچستان",
        "Federal Capital Territory": "وفاقی دارالحکومت",
        "Sector": "سیکٹر",
        "Road": "روڈ",
        "Gali": "گلی",
        "Street": "گلی",
        "Chowk": "چوک",
        "Market": "مارکیٹ"
    }
    for eng, urdu in replacements.items():
        pattern = re.compile(re.escape(eng), re.IGNORECASE)
        text = pattern.sub(urdu, text)
    return text
