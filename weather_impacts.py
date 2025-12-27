"""
Weather Impact Predictions Module
Calculates the impact of weather conditions on traffic, air quality, and pollen levels.
"""

from datetime import datetime
import math


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
    
    # Temperature effects (optimal pollen release: 15-25°C)
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
