import random
from datetime import datetime

def get_outfit_suggestion(temperature, condition, precipitation_prob=0, activity="casual", wind_speed=0):
    condition_lower = condition.lower()
    outfit = {"items": [], "accessories": [], "footwear": "", "description": "", "image_prompt": ""}
    
    if temperature < 0:
        outfit["items"], outfit["footwear"], outfit["accessories"], temp_desc = ["Heavy winter coat", "Thermal layers", "Thick sweater", "Warm pants"], "Insulated winter boots", ["Warm hat", "Scarf", "Gloves"], "freezing cold"
    elif temperature < 10:
        outfit["items"], outfit["footwear"], outfit["accessories"], temp_desc = ["Winter jacket", "Long-sleeve shirt", "Sweater", "Jeans or warm pants"], "Closed-toe shoes or boots", ["Light scarf", "Beanie"], "cold"
    elif temperature < 15:
        outfit["items"], outfit["footwear"], outfit["accessories"], temp_desc = ["Light jacket or cardigan", "Long-sleeve shirt", "Jeans"], "Sneakers or casual shoes", ["Light jacket"], "cool"
    elif temperature < 20:
        outfit["items"], outfit["footwear"], outfit["accessories"], temp_desc = ["Light sweater or hoodie", "T-shirt", "Jeans or casual pants"], "Sneakers", [], "mild"
    elif temperature < 25:
        outfit["items"], outfit["footwear"], outfit["accessories"], temp_desc = ["T-shirt or blouse", "Light pants or jeans"], "Sneakers or loafers", ["Sunglasses"], "pleasant"
    elif temperature < 30:
        outfit["items"], outfit["footwear"], outfit["accessories"], temp_desc = ["Light t-shirt", "Shorts or light pants"], "Sandals or breathable sneakers", ["Sunglasses", "Sun hat"], "warm"
    else:
        outfit["items"], outfit["footwear"], outfit["accessories"], temp_desc = ["Breathable light clothing", "Shorts", "Tank top or light t-shirt"], "Sandals or flip-flops", ["Sunglasses", "Wide-brim hat", "Sunscreen"], "hot"
    
    if 'rain' in condition_lower or 'drizzle' in condition_lower or precipitation_prob > 50:
        outfit["accessories"].extend(["Umbrella", "Waterproof jacket"])
        outfit["footwear"], weather_desc = "Waterproof boots or shoes", "rainy"
    elif 'snow' in condition_lower:
        outfit["accessories"].extend(["Waterproof gloves", "Snow boots"])
        outfit["footwear"], weather_desc = "Insulated snow boots", "snowy"
    elif 'cloud' in condition_lower: weather_desc = "cloudy"
    elif 'clear' in condition_lower or 'sun' in condition_lower:
        weather_desc = "sunny"
        if temperature > 20: outfit["accessories"].append("Sunscreen")
    else: weather_desc = condition_lower
    
    if wind_speed > 10: outfit["accessories"].append("Windbreaker")
    
    if activity in ["work", "formal"]:
        outfit["items"] = [item.replace("T-shirt", "Dress shirt").replace("Jeans", "Dress pants") for item in outfit["items"]]
        outfit["footwear"], activity_desc = outfit["footwear"].replace("Sneakers", "Dress shoes"), "professional"
    elif activity == "outdoor":
        outfit["items"].append("Athletic wear")
        outfit["footwear"], outfit["accessories"].append("Backpack")
        outfit["footwear"], activity_desc = "Hiking boots or athletic shoes", "outdoor adventure"
    else: activity_desc = "casual"
    
    outfit["description"] = f"For this {temp_desc} and {weather_desc} weather ({temperature}°C), we recommend {activity_desc} attire. Layer with {', '.join(outfit['items'][:2])} and wear {outfit['footwear']}. "
    if outfit["accessories"]: outfit["description"] += f"Don't forget: {', '.join(outfit['accessories'])}."
    
    outfit["image_prompt"] = (f"A stylish {activity_desc} outfit laid out on a clean surface, featuring {', '.join(outfit['items'][:3])}, {outfit['footwear']}, "
                             f"and {', '.join(outfit['accessories'][:2]) if outfit['accessories'] else 'minimal accessories'}. "
                             f"Modern fashion photography, {weather_desc} weather theme, professional lighting, flat lay composition, high quality, detailed textures")
    return outfit

RECIPE_DATABASE = {
    "cold": [
        {"name": "Classic Chicken Noodle Soup", "description": "Warm, comforting soup perfect for cold weather.", "prep_time": "45 min", "servings": 6, "difficulty": "Easy", "ingredients": ["chicken", "noodles", "carrots", "celery", "onion", "chicken broth"], "meal_type": ["lunch", "dinner"], "image_prompt": "A steaming bowl of chicken noodle soup with vegetables, warm lighting, cozy atmosphere"},
        {"name": "Beef Stew with Root Vegetables", "description": "Hearty and filling stew that warms you from the inside out.", "prep_time": "2 hours", "servings": 8, "difficulty": "Medium", "ingredients": ["beef", "potatoes", "carrots", "onions", "beef broth", "herbs"], "meal_type": ["dinner"], "image_prompt": "Rich beef stew in a rustic bowl with chunks of vegetables, steam rising"},
        {"name": "Hot Chocolate with Marshmallows", "description": "Rich, creamy hot chocolate topped with fluffy marshmallows.", "prep_time": "10 min", "servings": 2, "difficulty": "Easy", "ingredients": ["milk", "cocoa powder", "sugar", "marshmallows", "vanilla"], "meal_type": ["snack", "breakfast"], "image_prompt": "Mug of hot chocolate with marshmallows, whipped cream, cozy winter setting"}
    ],
    "hot": [
        {"name": "Greek Salad with Grilled Chicken", "description": "Light, refreshing salad perfect for hot summer days.", "prep_time": "20 min", "servings": 4, "difficulty": "Easy", "ingredients": ["lettuce", "tomatoes", "cucumber", "feta cheese", "olives", "chicken"], "meal_type": ["lunch", "dinner"], "image_prompt": "Fresh Greek salad with grilled chicken, colorful vegetables, bright summer lighting"},
        {"name": "Watermelon Mint Cooler", "description": "Refreshing drink to beat the heat. Hydrating and delicious.", "prep_time": "10 min", "servings": 4, "difficulty": "Easy", "ingredients": ["watermelon", "mint", "lime", "ice", "honey"], "meal_type": ["snack", "breakfast"], "image_prompt": "Glass of watermelon mint cooler with ice, fresh mint leaves, summer vibes"}
    ],
    "rainy": [
        {"name": "Tomato Basil Soup with Grilled Cheese", "description": "Classic comfort combo perfect for rainy days.", "prep_time": "30 min", "servings": 4, "difficulty": "Easy", "ingredients": ["tomatoes", "basil", "cream", "bread", "cheese", "butter"], "meal_type": ["lunch", "dinner"], "image_prompt": "Tomato soup in a bowl with grilled cheese sandwich, rainy day comfort food"},
        {"name": "Chai Tea Latte", "description": "Spiced tea latte to warm you up on a rainy afternoon.", "prep_time": "15 min", "servings": 2, "difficulty": "Easy", "ingredients": ["black tea", "milk", "cinnamon", "ginger", "cardamom", "honey"], "meal_type": ["snack", "breakfast"], "image_prompt": "Chai tea latte in a mug with cinnamon stick, cozy rainy day setting"}
    ],
    "mild": [
        {"name": "Quinoa Buddha Bowl", "description": "Nutritious bowl packed with colorful vegetables and protein.", "prep_time": "30 min", "servings": 2, "difficulty": "Easy", "ingredients": ["quinoa", "chickpeas", "avocado", "sweet potato", "kale", "tahini"], "meal_type": ["lunch", "dinner"], "image_prompt": "Colorful Buddha bowl with quinoa and vegetables, healthy and vibrant"},
        {"name": "Margherita Pizza", "description": "Classic pizza with fresh mozzarella, tomatoes, and basil.", "prep_time": "45 min", "servings": 4, "difficulty": "Medium", "ingredients": ["pizza dough", "mozzarella", "tomatoes", "basil", "olive oil"], "meal_type": ["lunch", "dinner"], "image_prompt": "Margherita pizza fresh from the oven, melted cheese, fresh basil leaves"}
    ]
}

def get_weather_category(temperature, condition):
    condition_lower = condition.lower()
    if 'rain' in condition_lower or 'drizzle' in condition_lower or 'shower' in condition_lower: return "rainy"
    if temperature < 10: return "cold"
    elif temperature > 28: return "hot"
    else: return "mild"

def get_recipe_suggestions(temperature, condition, meal_type=None, count=3):
    category = get_weather_category(temperature, condition)
    recipes = RECIPE_DATABASE.get(category, RECIPE_DATABASE["mild"])
    if meal_type:
        filtered = [r for r in recipes if meal_type.lower() in r["meal_type"]]
        if filtered: recipes = filtered
    selected = random.sample(recipes, min(count, len(recipes)))
    context = get_weather_context(temperature, condition, category)
    for r in selected:
        r["weather_context"], r["weather_category"] = context, category
    return selected

def get_weather_context(temperature, condition, category):
    contexts = {
        "cold": f"It's a chilly {temperature}°C outside. Warm up with these comforting dishes!",
        "hot": f"Beat the {temperature}°C heat with these refreshing, light meals!",
        "rainy": f"Perfect weather for cozy comfort food. Stay dry and enjoy!",
        "mild": f"Beautiful {temperature}°C weather! These balanced meals are perfect for today."
    }
    return contexts.get(category, "Enjoy these delicious recipes!")

def get_seasonal_recipes(month=None):
    if month is None: month = datetime.now().month
    if month in [12, 1, 2]: return RECIPE_DATABASE["cold"]
    elif month in [3, 4, 5]: return RECIPE_DATABASE["mild"]
    elif month in [6, 7, 8]: return RECIPE_DATABASE["hot"]
    else: return RECIPE_DATABASE["mild"] + RECIPE_DATABASE["rainy"][:2]

def format_recipe_for_display(recipe):
    return {
        "name": recipe["name"], "description": recipe["description"], "prepTime": recipe["prep_time"],
        "servings": recipe["servings"], "difficulty": recipe["difficulty"], "ingredients": recipe["ingredients"],
        "mealType": recipe["meal_type"], "weatherContext": recipe.get("weather_context", ""), "imagePrompt": recipe.get("image_prompt", "")
    }
