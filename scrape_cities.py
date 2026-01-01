import requests
from bs4 import BeautifulSoup
import json
import os
import re

URL = "https://service.unece.org/trade/locode/pk.htm"
OUTPUT_FILE = r"d:\SynoCast\assets\pakistan_cities.json"

def clean_text(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()


def scrape_cities():
    print(f"Fetching {URL}...")
    try:
        response = requests.get(URL, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return {"success": False, "message": str(e), "count": 0}

    soup = BeautifulSoup(response.content, 'html.parser')
    
    cities = []
    
    tables = soup.find_all('table')
    target_table = None
    
    for table in tables:
        if "LOCODE" in table.text and "Name" in table.text:
            target_table = table
            break
            
    if not target_table:
        if tables:
            tables.sort(key=lambda t: len(str(t)), reverse=True)
            target_table = tables[0]
        else:
            return {"success": False, "message": "No data table found", "count": 0}

    rows = target_table.find_all('tr')
    
    count = 0
    for row in rows:
        cols = row.find_all('td')
        if not cols or len(cols) < 4:
            continue
            
        locode_raw = clean_text(cols[1].text)
        name = clean_text(cols[2].text)
        subdiv = clean_text(cols[4].text) if len(cols) > 4 else ""
        function = clean_text(cols[5].text) if len(cols) > 5 else ""
        coordinates = clean_text(cols[9].text) if len(cols) > 9 else ""
        
        if not name or name == "Name":
            continue

        city_data = {
            "locode": locode_raw,
            "name": name,
            "subdiv": subdiv,
            "function": function,
            "coordinates": coordinates
        }
        cities.append(city_data)
        count += 1
            
    # Save to absolute path derived from this file location
    output_path = os.path.join(os.path.dirname(__file__), 'assets', 'pakistan_cities.json')
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cities, f, indent=2)
    except Exception as e:
        return {"success": False, "message": f"File save error: {e}", "count": count}

    return {"success": True, "message": "Scraping completed successfully", "count": count}

if __name__ == "__main__":
    result = scrape_cities()
    print(result)
