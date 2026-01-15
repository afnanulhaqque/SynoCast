import requests
import json
import logging
from datetime import datetime
from google import genai

logger = logging.getLogger(__name__)

NEWS_CACHE = {}
AI_NEWS_CACHE = {}
NEWS_CACHE_DURATION = 3600
AI_CACHE_DURATION = 300 # 5 minutes for AI categorization

def get_dummy_news():
    """Helper to return high-quality dummy weather news when API fails."""
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
        },
        {
            "title": "New Study Reveals Accelerated Melting of Arctic Sea Ice",
            "description": "Researchers warn that the Arctic could see ice-free summers much sooner than previously predicted, with serious global implications.",
            "url": "#",
            "urlToImage": "https://images.unsplash.com/photo-1581093196277-9f60807dbf06?q=80&w=1000&auto=format&fit=crop",
            "publishedAt": datetime.now().isoformat(),
            "source": {"name": "EcoToday"}
        },
        {
            "title": "Monsoon Rainfall Patterns Shifting Due to Climate Variability",
            "description": "Recent data suggests that the intensity and timing of monsoons are changing, affecting agriculture in several South Asian countries.",
            "url": "#",
            "urlToImage": "https://images.unsplash.com/photo-1534274988757-a28bf1f53ee1?q=80&w=1000&auto=format&fit=crop",
            "publishedAt": datetime.now().isoformat(),
            "source": {"name": "WorldWeather"}
        }
    ]

def fetch_weather_news(query="weather", country=None, page_size=10, api_key=None):
    if not api_key:
        return get_dummy_news()
        
    cache_key = f"{query}_{country}_{page_size}"
    if cache_key in NEWS_CACHE:
        cached = NEWS_CACHE[cache_key]
        if datetime.now().timestamp() - cached["timestamp"] < NEWS_CACHE_DURATION:
            return cached["articles"]

    try:
        essential_weather = "(weather OR climate OR storm OR forecast OR temperature OR rainfall OR snowfall OR earthquake OR flood OR drought OR hurricane OR cyclone OR typhoon OR wildfire OR heatwave OR coldwave OR meteorology OR blizzard OR tornado)"
        
        if query and "weather" not in query.lower():
            q = f"({query}) AND ({essential_weather})"
        else:
            q = query if query else essential_weather
            
        params = {
            "q": q,
            "pageSize": page_size * 2,
            "apiKey": api_key,
            "language": "en",
            "sortBy": "relevance"
        }
        
        response = requests.get("https://newsapi.org/v2/everything", params=params, timeout=10)
        
        if response.status_code in [429, 426]:
             logger.warning(f"NewsAPI Limit Hit ({response.status_code}). Using dummy data.")
             return get_dummy_news()
             
        if response.status_code in [401, 403]:
             logger.error(f"NewsAPI Auth Error ({response.status_code}). Check API Key.")
             return get_dummy_news()
             
        if not response.ok:
            logger.error(f"NewsAPI error: {response.status_code} - {response.text}")
            return []
            
        articles = [a for a in response.json().get("articles", []) 
                    if a.get("title") and a.get("title") != "[Removed]"]
        
        weather_terms = ['weather', 'forecast', 'storm', 'rain', 'snow', 'temp', 'climate', 'flood', 
                         'drought', 'heat', 'cold', 'wind', 'degree', 'celsius', 'fahrenheit', 
                         'monsoon', 'cyclone', 'typhoon', 'hurricane', 'blizzard', 'meteorology']
        
        filtered_articles = []
        for a in articles:
            text = (a.get('title', '') + ' ' + (a.get('description') or '')).lower()
            if any(term in text for term in weather_terms):
                filtered_articles.append(a)
            elif len(filtered_articles) < 3:
                filtered_articles.append(a)

        results = filtered_articles[:page_size]

        if not results:
            logger.info("No weather results found from API. Using dummy news.")
            return get_dummy_news()

        NEWS_CACHE[cache_key] = {
            "timestamp": datetime.now().timestamp(),
            "articles": results
        }
        return results
    except Exception as e:
        logger.error(f"News fetch error: {e}")
        return []

def fetch_gnews_weather(query="weather", page_size=10, api_key=None):
    if not api_key:
        logger.warning("No GNews API key provided.")
        return get_dummy_news()

    cache_key = f"gnews_{query}_{page_size}"
    if cache_key in NEWS_CACHE:
        cached = NEWS_CACHE[cache_key]
        if datetime.now().timestamp() - cached["timestamp"] < NEWS_CACHE_DURATION:
            return cached["articles"]

    try:
        url = "https://gnews.io/api/v4/search"
        if "pakistan" not in query.lower():
            q = f"{query} AND Pakistan"
        else:
            q = query
            
        params = {
            "q": q,
            "lang": "en",
            "max": page_size,
            "apikey": api_key,
            "country": "pk"
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if not response.ok:
            logger.error(f"GNews API error: {response.status_code} - {response.text}")
            return get_dummy_news()
            
        data = response.json()
        raw_articles = data.get("articles", [])
        
        formatted_articles = []
        for a in raw_articles:
            formatted_articles.append({
                "title": a.get("title"),
                "description": a.get("description"),
                "url": a.get("url"),
                "urlToImage": a.get("image"),
                "publishedAt": a.get("publishedAt"),
                "source": {"name": a.get("source", {}).get("name")},
                "location": "Pakistan",
                "urgency": "Medium"
            })
            
        NEWS_CACHE[cache_key] = {
            "timestamp": datetime.now().timestamp(),
            "articles": formatted_articles
        }
        
        if not formatted_articles:
             return get_dummy_news()
             
        return formatted_articles

    except Exception as e:
        logger.error(f"GNews fetch error: {e}")
        return get_dummy_news()

def categorize_news_with_ai(articles, api_key):
    if not articles:
        return []

    titles_hash = hash(tuple(a.get('title', '') for a in articles[:15]))
    now_ts = datetime.now().timestamp()
    
    if titles_hash in AI_NEWS_CACHE:
        cached = AI_NEWS_CACHE[titles_hash]
        if now_ts - cached["timestamp"] < AI_CACHE_DURATION:
            logger.info("Serving categorized news from AI cache")
            return cached["data"]

    if not api_key:
        weather_terms = ['weather', 'forecast', 'storm', 'rain', 'snow', 'temp', 'climate', 'flood', 
                         'drought', 'heat', 'cold', 'wind', 'degree', 'celsius', 'fahrenheit', 'monsoon', 'cyclone']
        
        fallback_results = []
        for a in articles:
            text = (a.get('title', '') + ' ' + a.get('description', '')).lower()
            if not any(term in text for term in weather_terms):
                continue

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
        client = genai.Client(api_key=api_key)
        
        article_summaries = []
        for a in articles[:15]:
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
        You are a strict weather news filter. Analyze the following news articles. 
        Discard ANY article that is not explicitly about:
        - Weather phenomena (rain, snow, wind, storms, etc.)
        - Climate change or global warming
        - Natural disasters (floods, droughts, earthquakes, wildfires)
        - Meteorological forecasts or reports
        - Environmental climate impact
        
        If an article is about politics, entertainment, general technology, or sports (unless directly weather-impacted), DISCARD it.
        
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

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt
        )
        content = response.text.strip()
        
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()

        categorized_articles = json.loads(content)
        results = []
        if isinstance(categorized_articles, list):
            results = categorized_articles
        elif isinstance(categorized_articles, dict) and "articles" in categorized_articles:
            results = categorized_articles["articles"]
        
        if results:
            AI_NEWS_CACHE[titles_hash] = {
                "timestamp": now_ts,
                "data": results
            }
            return results
        
        raise ValueError("AI response is not a valid list")

    except Exception as e:
        logger.error(f"AI categorization error: {e}")
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
