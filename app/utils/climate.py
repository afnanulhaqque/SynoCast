import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

HISTORICAL_CACHE = {}
HISTORICAL_CACHE_DURATION = 86400  # 24 hours

def fetch_historical_weather(lat, lon, date):
    try:
        if isinstance(date, datetime):
            date_str = date.strftime('%Y-%m-%d')
        else:
            date_str = date
        
        cache_key = f"hist_{lat}_{lon}_{date_str}"
        now_ts = datetime.now().timestamp()
        
        if cache_key in HISTORICAL_CACHE:
            cached = HISTORICAL_CACHE[cache_key]
            if now_ts - cached["timestamp"] < HISTORICAL_CACHE_DURATION:
                logger.info(f"Serving historical data for {date_str} from cache")
                return cached["data"]
        
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
    try:
        cache_key = f"normals_{lat}_{lon}_{month}"
        now_ts = datetime.now().timestamp()
        
        if cache_key in HISTORICAL_CACHE:
            cached = HISTORICAL_CACHE[cache_key]
            if now_ts - cached["timestamp"] < HISTORICAL_CACHE_DURATION * 7:
                return cached["data"]
        
        current_year = datetime.now().year
        start_date = f"{current_year - 30}-{month:02d}-01"
        end_date = f"{current_year}-{month:02d}-28"
        
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
                
                HISTORICAL_CACHE[cache_key] = {
                    "timestamp": now_ts,
                    "data": result
                }
                
                return result
        
        lat_abs = abs(lat)
        if lat_abs < 23.5: base_temp = 27
        elif lat_abs < 40: base_temp = 20
        elif lat_abs < 60: base_temp = 12
        else: base_temp = 0
        
        if month in [12, 1, 2]: seasonal_adj = -5 if lat > 0 else 5
        elif month in [6, 7, 8]: seasonal_adj = 5 if lat > 0 else -5
        else: seasonal_adj = 0
        
        return {
            "month": month,
            "temp_max_avg": base_temp + seasonal_adj + 5,
            "temp_min_avg": base_temp + seasonal_adj - 5,
            "temp_mean_avg": base_temp + seasonal_adj,
            "precipitation_avg": 50,
            "source": "Estimated (latitude-based)"
        }
        
    except Exception as e:
        logger.error(f"Climate normals fetch error: {e}")
        return None

def calculate_climate_anomaly(current_temp, normal_temp):
    try:
        if current_temp is None or normal_temp is None:
            return None
        
        anomaly = current_temp - normal_temp
        
        if anomaly > 5: interpretation = "Extreme Heat Anomaly"
        elif anomaly > 2: interpretation = "Above Normal"
        elif anomaly < -5: interpretation = "Extreme Cold Anomaly"
        elif anomaly < -2: interpretation = "Below Normal"
        else: interpretation = "Near Normal"
        
        return {
            "value": round(anomaly, 1),
            "interpretation": interpretation,
            "is_significant": abs(anomaly) > 2
        }
    except Exception as e:
        logger.error(f"Climate anomaly calculation error: {e}")
        return None

def analyze_seasonal_trends(lat, lon, years_back=5):
    try:
        current_year = datetime.now().year
        trends = []
        
        for i in range(1, years_back + 1):
            year = current_year - i
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"
            
            url = f"https://archive-api.open-meteo.com/v1/archive"
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": start_date,
                "end_date": end_date,
                "daily": "temperature_2m_mean,precipitation_sum",
                "timezone": "auto"
            }
            
            response = requests.get(url, params=params, timeout=15)
            if response.ok:
                data = response.json()
                if data.get('daily'):
                    avg_temp = sum(data['daily']['temperature_2m_mean']) / len(data['daily']['temperature_2m_mean'])
                    total_precip = sum(data['daily']['precipitation_sum'])
                    trends.append({
                        "year": year,
                        "avg_temp": round(avg_temp, 1),
                        "total_precip": round(total_precip, 1)
                    })
        
        return trends
    except Exception as e:
        logger.error(f"Seasonal trends analysis error: {e}")
        return []

def get_record_temperatures(lat, lon, years_back=10):
    try:
        current_year = datetime.now().year
        start_date = f"{current_year - years_back}-01-01"
        end_date = f"{current_year-1}-12-31"
        
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
        if response.ok:
            data = response.json()
            if data.get('daily'):
                record_high = max(data['daily']['temperature_2m_max'])
                record_low = min(data['daily']['temperature_2m_min'])
                high_idx = data['daily']['temperature_2m_max'].index(record_high)
                low_idx = data['daily']['temperature_2m_min'].index(record_low)
                
                return {
                    "high": {"value": record_high, "date": data['daily']['time'][high_idx]},
                    "low": {"value": record_low, "date": data['daily']['time'][low_idx]},
                    "period_years": years_back
                }
        return None
    except Exception as e:
        logger.error(f"Record temperatures fetch error: {e}")
        return None
