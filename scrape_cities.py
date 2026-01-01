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
        response = requests.get(URL)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    
    cities = []
    
    # UNECE pages typically have the data in a table within the content
    # We will iterate all tables to find the one with the header "LOCODE"
    tables = soup.find_all('table')
    target_table = None
    
    for table in tables:
        # Check if this table has the header we expect
        if "LOCODE" in table.text and "Name" in table.text:
            target_table = table
            break
            
    if not target_table:
        print("Could not find the data table.")
        # Fallback: try the biggest table
        if tables:
            tables.sort(key=lambda t: len(str(t)), reverse=True)
            target_table = tables[0]
            print("Using the largest table found.")
        else:
            return

    rows = target_table.find_all('tr')
    print(f"Found table with {len(rows)} rows.")
    
    count = 0
    for row in rows:
        cols = row.find_all('td')
        # Typical UNECE structure:
        # 0: Ch (Change indicator)
        # 1: LOCODE (e.g., '   KHI')
        # 2: Name (e.g., 'Karachi')
        # 3: NameWoDiacritics
        # 4: SubDiv (e.g., 'SD')
        # 5: Function (e.g., '12345---')
        # 6: Status (e.g., 'AI')
        # 7: Date 
        # 8: IATA
        # 9: Coordinates (e.g., '2452N 06703E')
        # 10: Remarks
        
        if not cols or len(cols) < 4:
            continue
            
        # Extract data (assuming standard UNECE layout)
        # Sometimes there are empty spacer rows or headers in td
        
        locode_raw = clean_text(cols[1].text)
        name = clean_text(cols[2].text)
        subdiv = clean_text(cols[4].text) if len(cols) > 4 else ""
        function = clean_text(cols[5].text) if len(cols) > 5 else ""
        coordinates = clean_text(cols[9].text) if len(cols) > 9 else ""
        
        # Valid LOCODEs for PK usually look like "   KHI" or "PK KHI". 
        # The ISO code "PK" might be implied or present.
        # We will store the 3-letter code if possible, or full.
        # Let's clean up LOCODE.
        # If it's just 3 letters, we prepend PK? Or keep as is?
        # The user asked for "cities data", so the name is most important.
        
        if not name or name == "Name": # Skip header row if it wasn't valid th
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
            
    print(f"Extracted {len(cities)} cities.")
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(cities, f, indent=2)
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    scrape_cities()
