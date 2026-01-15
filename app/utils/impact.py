from datetime import datetime

def get_traffic_icon(score):
    if score >= 8: return "fa-circle-exclamation"
    elif score >= 5: return "fa-triangle-exclamation"
    elif score >= 3: return "fa-circle-info"
    else: return "fa-circle-check"

def calculate_traffic_impact(weather_data, temperature):
    condition = weather_data.get('main', 'Clear').lower()
    description = weather_data.get('description', '').lower()
    
    impact_score = 1
    impact_level = "Minimal"
    advice = "Normal traffic conditions expected."
    
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
    condition = weather_data.get('main', 'Clear').lower()
    if current_aqi is None: current_aqi = 50
    
    trend_modifier = 0
    if wind_speed > 5:
        trend_modifier -= 15
        trend_direction = "improving"
    elif wind_speed < 2:
        trend_modifier += 10
        trend_direction = "worsening"
    else:
        trend_direction = "stable"
    
    if 'rain' in condition:
        trend_modifier -= 20
        trend_direction = "improving significantly"
    
    if humidity > 80 and wind_speed < 3: trend_modifier += 10
    if temperature < 5 and wind_speed < 2:
        trend_modifier += 15
        trend_direction = "worsening"
    if temperature > 30: trend_modifier += 10
    
    predicted_aqi = max(0, min(500, current_aqi + trend_modifier))
    
    if predicted_aqi <= 50:
        category, advice, color = "Good", "Air quality is excellent. Perfect for outdoor activities!", "#00e400"
    elif predicted_aqi <= 100:
        category, advice, color = "Moderate", "Air quality is acceptable. Sensitive individuals should limit prolonged outdoor exertion.", "#ffff00"
    elif predicted_aqi <= 150:
        category, advice, color = "Unhealthy for Sensitive Groups", "People with respiratory conditions should reduce outdoor activities.", "#ff7e00"
    elif predicted_aqi <= 200:
        category, advice, color = "Unhealthy", "Everyone should reduce prolonged outdoor exertion.", "#ff0000"
    elif predicted_aqi <= 300:
        category, advice, color = "Very Unhealthy", "Avoid outdoor activities. Health alert for everyone.", "#8f3f97"
    else:
        category, advice, color = "Hazardous", "Stay indoors. Emergency conditions for all.", "#7e0023"
    
    return {
        "current_aqi": current_aqi,
        "predicted_aqi": round(predicted_aqi),
        "trend": trend_direction,
        "category": category,
        "advice": advice,
        "color": color
    }

def calculate_pollen_count(temperature, humidity, wind_speed, weather_condition, month=None):
    if month is None: month = datetime.now().month
    pollen_score = 0
    
    if month in [3, 4, 5]: pollen_score, pollen_type = 7, "tree pollen"
    elif month in [6, 7, 8]: pollen_score, pollen_type = 6, "grass pollen"
    elif month in [9, 10]: pollen_score, pollen_type = 5, "ragweed"
    else: pollen_score, pollen_type = 1, "general allergens"
    
    if 15 <= temperature <= 25: pollen_score += 2
    elif temperature < 10 or temperature > 30: pollen_score -= 2
    
    if humidity > 70: pollen_score -= 2
    elif humidity < 40: pollen_score += 1
    
    if 2 <= wind_speed <= 5: pollen_score += 2
    elif wind_speed > 8: pollen_score -= 1
    
    condition_lower = weather_condition.lower()
    if 'rain' in condition_lower: pollen_score -= 3
    elif 'clear' in condition_lower or 'sun' in condition_lower: pollen_score += 1
    
    pollen_score = max(0, min(10, pollen_score))
    
    if pollen_score <= 2:
        level, advice, color = "Low", "Great day for allergy sufferers! Minimal pollen in the air.", "#00e400"
    elif pollen_score <= 4:
        level, advice, color = "Low-Moderate", "Pollen levels are manageable. Sensitive individuals may experience mild symptoms.", "#92d050"
    elif pollen_score <= 6:
        level, advice, color = "Moderate", "Pollen levels are manageable. Consider taking allergy medication if needed.", "#ffff00"
    elif pollen_score <= 8:
        level, advice, color = "High", "High pollen count. Allergy sufferers should take precautions and limit outdoor time.", "#ff7e00"
    else:
        level, advice, color = "Very High", "Very high pollen levels. Keep windows closed and avoid outdoor activities if allergic.", "#ff0000"
    
    return {
        "score": pollen_score,
        "level": level,
        "type": pollen_type,
        "advice": advice,
        "color": color
    }

def get_all_impacts(weather_data, temperature, humidity, wind_speed, current_aqi=None):
    return {
        "traffic": calculate_traffic_impact(weather_data, temperature),
        "air_quality": calculate_air_quality_prediction(weather_data, temperature, humidity, wind_speed, current_aqi),
        "pollen": calculate_pollen_count(temperature, humidity, wind_speed, weather_data.get('main', 'Clear'))
    }
