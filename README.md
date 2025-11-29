# SynoCast

SynoCast is a lightweight Flask prototype for a weather storytelling hub. It serves a marketing-style landing page, a curated newsroom, and a placeholder weather dashboard while dynamically showing the visitor’s local date, time, and timezone based on their IP address.

**Live Preview:** [https://syno-cast.vercel.app/](https://syno-cast.vercel.app/)

## Features

- Landing page that highlights the WeatherTrip brand story with hero banners and promotional content.
- News page that showcases breaking and featured weather stories using static sample data and imagery.
- Weather page scaffold ready for detailed forecast cards.
- **New:** Map & Calendar page featuring an interactive map (Leaflet.js) and a personal event calendar (FullCalendar).
- **New:** Multi-channel subscription system supporting both Email (via Resend) and WhatsApp (via Twilio/Mock) with OTP verification.
- **New:** AI-powered Chatbot integrated with Google's Gemini API for intelligent weather and event advice.
- Reusable Bootstrap 5 layout with Font Awesome icons and a custom theme located in `assests/styles/style.css`.
- Geo-aware header that displays `request`-based local time using the [ipapi.co](https://ipapi.co) lookup service with graceful fallback for localhost.
- In-page chatbot modal with a demo `/chat` endpoint for local testing — implemented in `templates/base.html`, `assests/js/chatbot_modal.js`, and CSS in `assests/styles/style.css`.

## Tech Stack

- Python 3.10+
- Flask (compatible with Flask 3.x)
- SQLite (Database)
- Bootstrap 5 / Font Awesome
- Leaflet.js (Interactive Maps)
- FullCalendar (Event Management)
- Google Gemini API (AI Chatbot)
- Resend API (Email)
- Twilio API (WhatsApp - optional/mockable)
- ipapi.co (public REST API)

## Project Structure

```
app.py                 # Flask app with three routes and timezone helper
templates/             # Jinja templates (base + page-specific)
assests/               # Static images, icons, and custom CSS
```

## Getting Started

1. **Create & activate a virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. **Install dependencies**
   ```bash
   pip install flask requests google-generativeai resend twilio
   ```
3. **Run the development server**
   ```bash
   set FLASK_APP=app.py
   flask run --debug
   ```
   The site will be available at [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Customization Tips

- Replace placeholder card copy, dates, and URLs in `templates/home.html`, `templates/news.html`, and `templates/weather.html`.
- Update images or branding assets in `assests/`.
- Expand `weather.html` with real forecast data (e.g., by consuming a weather API) and wire it into `app.py`.

## AI Chatbot

- The chatbot is now powered by **Google's Gemini API**, capable of providing weather-aware advice and event planning tips.
- The UI is located in `templates/base.html` and `assests/js/chatbot_modal.js`.
- The backend logic in `app.py` handles context management and API interaction.
- To use the AI features, ensure you have a valid `GEMINI_API_KEY` set in your environment or `app.py`.

## Deployment Notes

- Netlify is static-only and cannot host a Python Flask app. Use Render, Railway, Fly, or PythonAnywhere to host a full Flask app.
- Example `Procfile` for hosting (create a file named `Procfile` if deploying to Render/Heroku):

  ```text
  web: gunicorn app:app --bind 0.0.0.0:$PORT
  ```

- For production, pin dependencies (e.g., `Flask==3.1.2`) in `requirements.txt` and use a production WSGI server. Consider migrating to Postgres or another managed DB rather than SQLite for production deployments.

## Changelog

- 2025-11-30: Added WhatsApp subscription with OTP, integrated Google Gemini AI for chatbot, added Map & Calendar page, updated UI styling.
- 2025-11-26: Added in-page chatbot modal (UI + JS) with a demo `/chat` endpoint; updated DB initialization to be import-time for Flask 3 compatibility, added modal CSS for message bubbles and consistent input/button heights.

## License

This project currently has no explicit license. Add one before distributing or deploying publicly.
