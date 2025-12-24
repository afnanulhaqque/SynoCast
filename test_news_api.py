import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("NEWS_API_KEY")

def test_news(query):
    weather_keywords = "(weather OR climate OR storm OR forecast OR temperature OR rainfall OR snowfall OR earthquake OR flood OR drought OR hurricane OR cyclone OR typhoon OR wildfire OR heatwave OR coldwave OR meteorology OR blizzard OR tornado)"
    refined_query = f"{query} AND {weather_keywords}"
    
    params = {
        "q": refined_query,
        "pageSize": 5,
        "apiKey": api_key,
        "language": "en",
        "sortBy": "relevance"
    }
    
    print(f"Testing query: {refined_query}")
    try:
        response = requests.get("https://newsapi.org/v2/everything", params=params, timeout=10)
        print(f"Status: {response.status_code}")
        data = response.json()
        articles = data.get("articles", [])
        print(f"Total results: {data.get('totalResults', 0)}")
        print(f"Num articles returned: {len(articles)}")
        for i, a in enumerate(articles):
            print(f"{i+1}. {a.get('title')}")
    except Exception as e:
        print(f"Error: {e}")

if api_key:
    test_news("Islamabad")
    test_news("weather extreme events")
else:
    print("No NEWS_API_KEY found")
