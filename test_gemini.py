import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("GEMINI_API_KEY not found in .env")
else:
    print(f"GEMINI_API_KEY found: {api_key[:5]}...{api_key[-5:]}")
    try:
        genai.configure(api_key=api_key)
        print("--- Testing gemini-flash-latest ---")
        try:
            model = genai.GenerativeModel("gemini-flash-latest")
            response = model.generate_content("Hello, are you working?")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")


    except Exception as e:
        print(f"General Error: {e}")





