"""
Weather-Based Recipe Suggestions Module
Recommends recipes based on current weather conditions and temperature.
"""

import random
from datetime import datetime


# Recipe database categorized by weather conditions
RECIPE_DATABASE = {
    "cold": [
        {
            "name": "Classic Chicken Noodle Soup",
            "description": "Warm, comforting soup perfect for cold weather. A timeless remedy for chilly days.",
            "prep_time": "45 min",
            "servings": 6,
            "difficulty": "Easy",
            "ingredients": ["chicken", "noodles", "carrots", "celery", "onion", "chicken broth"],
            "meal_type": ["lunch", "dinner"],
            "image_prompt": "A steaming bowl of chicken noodle soup with vegetables, warm lighting, cozy atmosphere"
        },
        {
            "name": "Beef Stew with Root Vegetables",
            "description": "Hearty and filling stew that warms you from the inside out.",
            "prep_time": "2 hours",
            "servings": 8,
            "difficulty": "Medium",
            "ingredients": ["beef", "potatoes", "carrots", "onions", "beef broth", "herbs"],
            "meal_type": ["dinner"],
            "image_prompt": "Rich beef stew in a rustic bowl with chunks of vegetables, steam rising"
        },
        {
            "name": "Hot Chocolate with Marshmallows",
            "description": "Rich, creamy hot chocolate topped with fluffy marshmallows.",
            "prep_time": "10 min",
            "servings": 2,
            "difficulty": "Easy",
            "ingredients": ["milk", "cocoa powder", "sugar", "marshmallows", "vanilla"],
            "meal_type": ["snack", "breakfast"],
            "image_prompt": "Mug of hot chocolate with marshmallows, whipped cream, cozy winter setting"
        },
        {
            "name": "Baked Mac and Cheese",
            "description": "Creamy, cheesy comfort food with a crispy golden top.",
            "prep_time": "40 min",
            "servings": 6,
            "difficulty": "Easy",
            "ingredients": ["pasta", "cheddar cheese", "milk", "butter", "breadcrumbs"],
            "meal_type": ["lunch", "dinner"],
            "image_prompt": "Baked mac and cheese with golden crispy top, cheese bubbling, comfort food"
        },
        {
            "name": "Chili Con Carne",
            "description": "Spicy, warming chili packed with beans and ground beef.",
            "prep_time": "1 hour",
            "servings": 8,
            "difficulty": "Easy",
            "ingredients": ["ground beef", "kidney beans", "tomatoes", "chili peppers", "onions"],
            "meal_type": ["lunch", "dinner"],
            "image_prompt": "Bowl of spicy chili con carne with beans, topped with cheese and sour cream"
        }
    ],
    "hot": [
        {
            "name": "Greek Salad with Grilled Chicken",
            "description": "Light, refreshing salad perfect for hot summer days.",
            "prep_time": "20 min",
            "servings": 4,
            "difficulty": "Easy",
            "ingredients": ["lettuce", "tomatoes", "cucumber", "feta cheese", "olives", "chicken"],
            "meal_type": ["lunch", "dinner"],
            "image_prompt": "Fresh Greek salad with grilled chicken, colorful vegetables, bright summer lighting"
        },
        {
            "name": "Watermelon Mint Cooler",
            "description": "Refreshing drink to beat the heat. Hydrating and delicious.",
            "prep_time": "10 min",
            "servings": 4,
            "difficulty": "Easy",
            "ingredients": ["watermelon", "mint", "lime", "ice", "honey"],
            "meal_type": ["snack", "breakfast"],
            "image_prompt": "Glass of watermelon mint cooler with ice, fresh mint leaves, summer vibes"
        },
        {
            "name": "Gazpacho (Cold Tomato Soup)",
            "description": "Chilled Spanish soup bursting with fresh vegetable flavors.",
            "prep_time": "15 min + chill time",
            "servings": 6,
            "difficulty": "Easy",
            "ingredients": ["tomatoes", "cucumber", "bell peppers", "onion", "garlic", "olive oil"],
            "meal_type": ["lunch", "snack"],
            "image_prompt": "Bowl of cold gazpacho soup, vibrant red color, garnished with vegetables"
        },
        {
            "name": "Caprese Salad",
            "description": "Simple Italian salad with fresh mozzarella, tomatoes, and basil.",
            "prep_time": "10 min",
            "servings": 4,
            "difficulty": "Easy",
            "ingredients": ["mozzarella", "tomatoes", "basil", "olive oil", "balsamic vinegar"],
            "meal_type": ["lunch", "snack"],
            "image_prompt": "Caprese salad with fresh mozzarella and tomatoes, drizzled with balsamic glaze"
        },
        {
            "name": "Grilled Fish Tacos",
            "description": "Light and flavorful tacos with grilled fish and fresh toppings.",
            "prep_time": "30 min",
            "servings": 4,
            "difficulty": "Medium",
            "ingredients": ["white fish", "tortillas", "cabbage", "lime", "avocado", "cilantro"],
            "meal_type": ["lunch", "dinner"],
            "image_prompt": "Grilled fish tacos with fresh toppings, colorful presentation, summer meal"
        }
    ],
    "rainy": [
        {
            "name": "Tomato Basil Soup with Grilled Cheese",
            "description": "Classic comfort combo perfect for rainy days.",
            "prep_time": "30 min",
            "servings": 4,
            "difficulty": "Easy",
            "ingredients": ["tomatoes", "basil", "cream", "bread", "cheese", "butter"],
            "meal_type": ["lunch", "dinner"],
            "image_prompt": "Tomato soup in a bowl with grilled cheese sandwich, rainy day comfort food"
        },
        {
            "name": "Creamy Mushroom Risotto",
            "description": "Rich, creamy risotto that's perfect for cozy indoor dining.",
            "prep_time": "45 min",
            "servings": 4,
            "difficulty": "Medium",
            "ingredients": ["arborio rice", "mushrooms", "parmesan", "white wine", "butter", "broth"],
            "meal_type": ["dinner"],
            "image_prompt": "Creamy mushroom risotto in a bowl, garnished with parmesan, elegant presentation"
        },
        {
            "name": "Chai Tea Latte",
            "description": "Spiced tea latte to warm you up on a rainy afternoon.",
            "prep_time": "15 min",
            "servings": 2,
            "difficulty": "Easy",
            "ingredients": ["black tea", "milk", "cinnamon", "ginger", "cardamom", "honey"],
            "meal_type": ["snack", "breakfast"],
            "image_prompt": "Chai tea latte in a mug with cinnamon stick, cozy rainy day setting"
        },
        {
            "name": "Chicken Pot Pie",
            "description": "Flaky pastry filled with creamy chicken and vegetables.",
            "prep_time": "1 hour",
            "servings": 6,
            "difficulty": "Medium",
            "ingredients": ["chicken", "puff pastry", "carrots", "peas", "cream", "potatoes"],
            "meal_type": ["dinner"],
            "image_prompt": "Golden chicken pot pie with flaky crust, steam escaping, comfort food"
        }
    ],
    "mild": [
        {
            "name": "Quinoa Buddha Bowl",
            "description": "Nutritious bowl packed with colorful vegetables and protein.",
            "prep_time": "30 min",
            "servings": 2,
            "difficulty": "Easy",
            "ingredients": ["quinoa", "chickpeas", "avocado", "sweet potato", "kale", "tahini"],
            "meal_type": ["lunch", "dinner"],
            "image_prompt": "Colorful Buddha bowl with quinoa and vegetables, healthy and vibrant"
        },
        {
            "name": "Margherita Pizza",
            "description": "Classic pizza with fresh mozzarella, tomatoes, and basil.",
            "prep_time": "45 min",
            "servings": 4,
            "difficulty": "Medium",
            "ingredients": ["pizza dough", "mozzarella", "tomatoes", "basil", "olive oil"],
            "meal_type": ["lunch", "dinner"],
            "image_prompt": "Margherita pizza fresh from the oven, melted cheese, fresh basil leaves"
        },
        {
            "name": "Chicken Caesar Wrap",
            "description": "Portable and delicious wrap perfect for outdoor activities.",
            "prep_time": "15 min",
            "servings": 2,
            "difficulty": "Easy",
            "ingredients": ["tortilla", "chicken", "romaine lettuce", "caesar dressing", "parmesan"],
            "meal_type": ["lunch"],
            "image_prompt": "Chicken caesar wrap cut in half, showing fresh ingredients, casual meal"
        },
        {
            "name": "Pasta Primavera",
            "description": "Light pasta dish with seasonal vegetables.",
            "prep_time": "25 min",
            "servings": 4,
            "difficulty": "Easy",
            "ingredients": ["pasta", "zucchini", "bell peppers", "cherry tomatoes", "garlic", "olive oil"],
            "meal_type": ["lunch", "dinner"],
            "image_prompt": "Pasta primavera with colorful vegetables, light and fresh, spring meal"
        }
    ]
}


def get_weather_category(temperature, condition):
    """
    Categorize weather into recipe-friendly categories.
    
    Args:
        temperature: Temperature in Celsius
        condition: Weather condition string
    
    Returns:
        String category: 'cold', 'hot', 'rainy', or 'mild'
    """
    condition_lower = condition.lower()
    
    # Rain takes precedence
    if 'rain' in condition_lower or 'drizzle' in condition_lower or 'shower' in condition_lower:
        return "rainy"
    
    # Temperature-based categories
    if temperature < 10:
        return "cold"
    elif temperature > 28:
        return "hot"
    else:
        return "mild"


def get_recipe_suggestions(temperature, condition, meal_type=None, count=3):
    """
    Get recipe suggestions based on weather conditions.
    
    Args:
        temperature: Temperature in Celsius
        condition: Weather condition string
        meal_type: Optional filter for meal type ('breakfast', 'lunch', 'dinner', 'snack')
        count: Number of recipes to return (default 3)
    
    Returns:
        List of recipe dictionaries with weather context
    """
    category = get_weather_category(temperature, condition)
    recipes = RECIPE_DATABASE.get(category, RECIPE_DATABASE["mild"])
    
    # Filter by meal type if specified
    if meal_type:
        filtered_recipes = [r for r in recipes if meal_type.lower() in r["meal_type"]]
        if filtered_recipes:
            recipes = filtered_recipes
    
    # Randomly select recipes
    selected_recipes = random.sample(recipes, min(count, len(recipes)))
    
    # Add weather context to each recipe
    weather_context = get_weather_context(temperature, condition, category)
    
    for recipe in selected_recipes:
        recipe["weather_context"] = weather_context
        recipe["weather_category"] = category
    
    return selected_recipes


def get_weather_context(temperature, condition, category):
    """
    Generate contextual message explaining why these recipes fit the weather.
    
    Args:
        temperature: Temperature in Celsius
        condition: Weather condition string
        category: Weather category
    
    Returns:
        String with weather context
    """
    contexts = {
        "cold": f"It's a chilly {temperature}°C outside. Warm up with these comforting dishes!",
        "hot": f"Beat the {temperature}°C heat with these refreshing, light meals!",
        "rainy": f"Perfect weather for cozy comfort food. Stay dry and enjoy!",
        "mild": f"Beautiful {temperature}°C weather! These balanced meals are perfect for today."
    }
    
    return contexts.get(category, "Enjoy these delicious recipes!")


def get_seasonal_recipes(month=None):
    """
    Get recipes appropriate for the current season.
    
    Args:
        month: Month number (1-12), defaults to current month
    
    Returns:
        List of seasonal recipe suggestions
    """
    if month is None:
        month = datetime.now().month
    
    # Determine season (Northern Hemisphere)
    if month in [12, 1, 2]:
        season = "winter"
        return RECIPE_DATABASE["cold"]
    elif month in [3, 4, 5]:
        season = "spring"
        return RECIPE_DATABASE["mild"]
    elif month in [6, 7, 8]:
        season = "summer"
        return RECIPE_DATABASE["hot"]
    else:  # 9, 10, 11
        season = "fall"
        return RECIPE_DATABASE["mild"] + RECIPE_DATABASE["rainy"][:2]


def format_recipe_for_display(recipe):
    """
    Format recipe data for frontend display.
    
    Args:
        recipe: Recipe dictionary
    
    Returns:
        Formatted recipe dictionary
    """
    return {
        "name": recipe["name"],
        "description": recipe["description"],
        "prepTime": recipe["prep_time"],
        "servings": recipe["servings"],
        "difficulty": recipe["difficulty"],
        "ingredients": recipe["ingredients"],
        "mealType": recipe["meal_type"],
        "weatherContext": recipe.get("weather_context", ""),
        "imagePrompt": recipe.get("image_prompt", "")
    }
