# SynoCast

SynoCast is a lightweight Flask prototype for a weather storytelling hub. It serves a marketing-style landing page, a curated newsroom, and a placeholder weather dashboard while dynamically showing the visitor’s local date, time, and timezone based on their IP address.

## Features

- Landing page that highlights the WeatherTrip brand story with hero banners and promotional content.
- News page that showcases breaking and featured weather stories using static sample data and imagery.
- Weather page scaffold ready for detailed forecast cards.
- Reusable Bootstrap 5 layout with Font Awesome icons and a custom theme located in `assests/styles/style.css`.
- Geo-aware header that displays `request`-based local time using the [ipapi.co](https://ipapi.co) lookup service with graceful fallback for localhost.

- In-page chatbot modal with a demo `/chat` endpoint for local testing — implemented in `templates/base.html`, `assests/js/chatbot_modal.js`, and CSS in `assests/styles/style.css`.
- Subscription system with Email OTP verification using a SQLite database (`subscriptions.db`).

## Tech Stack

- Python 3.10+
- Flask (compatible with Flask 3.x — the app initializes the database at import time to avoid relying on deprecated lifecycle decorators)
- Bootstrap 5 / Font Awesome
- ipapi.co (public REST API)
- SQLite (for storing subscriptions)

## Project Structure

```
app.py                 # Flask app with routes, timezone helper, and OTP logic
templates/             # Jinja templates (base + page-specific)
assests/               # Static images, icons, and custom CSS
subscriptions.db       # SQLite database for subscriptions (auto-created)
```

## Getting Started

1. **Create & activate a virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the development server**
   ```bash
   set FLASK_APP=app.py
   flask run --debug
   ```
   The site will be available at [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Customization Tips

- Replace placeholder card copy, dates, and URLs in `templates/home.html`, `templates/news.html`, `templates/weather.html`, and `templates/subscribe.html`.
- Update images or branding assets in `assests/`.
- Expand `weather.html` with real forecast data (e.g., by consuming a weather API) and wire it into `app.py`.

## Chatbot (demo)

- The repo includes a demo chatbot modal that opens from the navbar chat icon. The UI code is inside `templates/base.html` and `assests/js/chatbot_modal.js`.
- The server-side demo endpoint at `/chat` accepts POST JSON payloads (e.g., `{ "message": "Hello" }`) and returns a simple JSON reply `{"reply": "SynoCast: You said 'Hello'"}`.
- To extend the chatbot with a real AI backend, replace the `reply` generation in `app.py` with the appropriate API call.

## Deployment Notes

- Netlify is static-only and cannot host a Python Flask app. Use Render, Railway, Fly, or PythonAnywhere to host a full Flask app.
- Example `Procfile` for hosting (create a file named `Procfile` if deploying to Render/Heroku):

  ```text
  web: gunicorn app:app --bind 0.0.0.0:$PORT
  ```

- For production, pin dependencies (e.g., `Flask==3.1.2`) in `requirements.txt` and use a production WSGI server. Consider migrating to Postgres or another managed DB rather than SQLite for production deployments.

## Changelog

- 2025-11-26: Added in-page chatbot modal (UI + JS) with a demo `/chat` endpoint; updated DB initialization to be import-time for Flask 3 compatibility, added modal CSS for message bubbles and consistent input/button heights.
- 2025-11-29: Added Subscription feature with OTP verification and SQLite integration.

## License

This project currently has no explicit license. Add one before distributing or deploying publicly.
