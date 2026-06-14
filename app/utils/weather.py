import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

def aggregate_forecast_data(forecast_list, timezone_offset=0):
    daily_data = {}
    
    for item in forecast_list:
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

    sorted_dates = sorted(daily_data.keys())
    
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
    try:
        sunrise_local = datetime.fromtimestamp(sunrise_ts, tz=timezone.utc) + timedelta(seconds=timezone_offset)
        sunset_local = datetime.fromtimestamp(sunset_ts, tz=timezone.utc) + timedelta(seconds=timezone_offset)
        
        morning_start = sunrise_local
        morning_end = sunrise_local + timedelta(hours=1)
        
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
        else:
            return {"name": "Waning Crescent", "emoji": "🌘", "illumination": f"{int((1 - phase) * 100)}%"}
    except Exception as e:
        logger.error(f"Moon phase interpretation error: {e}")
        return {"name": "Unknown", "emoji": "🌑", "illumination": "N/A"}

def format_astronomy_data(daily_item, timezone_offset=0):
    try:
        sunrise_ts = daily_item.get('sunrise')
        sunset_ts = daily_item.get('sunset')
        moonrise_ts = daily_item.get('moonrise')
        moonset_ts = daily_item.get('moonset')
        moon_phase = daily_item.get('moon_phase', 0)
        
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
        
        if sunrise_ts and sunset_ts:
            golden_hours = calculate_golden_hours(sunrise_ts, sunset_ts, timezone_offset)
            if golden_hours:
                result["golden_hours"] = golden_hours
        
        return result
    except Exception as e:
        logger.error(f"Astronomy data formatting error: {e}")
        return None

def calculate_aqi(pm2_5, pm10):
    """
    Calculate US EPA AQI based on PM2.5 and PM10 values.
    Returns a dictionary with AQI value, label, and standard.
    """
    def calc_index(cp, breakpoints):
        for bp in breakpoints:
            if bp[0] <= cp <= bp[1]:
                return int(round(((bp[3] - bp[2]) / (bp[1] - bp[0])) * (cp - bp[0]) + bp[2]))
        return 500

    # Breakpoints: (C_low, C_high, I_low, I_high)
    pm25_bp = [
        (0.0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 350.4, 301, 400),
        (350.5, 500.4, 401, 500)
    ]

    pm10_bp = [
        (0, 54, 0, 50),
        (55, 154, 51, 100),
        (155, 254, 101, 150),
        (255, 354, 151, 200),
        (355, 424, 201, 300),
        (425, 504, 301, 400),
        (505, 604, 401, 500)
    ]

    aqi_pm25 = calc_index(pm2_5, pm25_bp)
    aqi_pm10 = calc_index(pm10, pm10_bp)

    aqi = max(aqi_pm25, aqi_pm10)

    if aqi <= 50:
        label = "Good"
    elif aqi <= 100:
        label = "Moderate"
    elif aqi <= 150:
        label = "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        label = "Unhealthy"
    elif aqi <= 300:
        label = "Very Unhealthy"
    else:
        label = "Hazardous"

    return {"value": aqi, "label": label, "standard": "US EPA"}

