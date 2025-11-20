# SynoCast

SynoCast is a lightweight Flask prototype for a weather storytelling hub. It serves a marketing-style landing page, a curated newsroom, and a placeholder weather dashboard while dynamically showing the visitor’s local date, time, and timezone based on their IP address.

## Features
- Landing page that highlights the WeatherTrip brand story with hero banners and promotional content.
- News page that showcases breaking and featured weather stories using static sample data and imagery.
- Weather page scaffold ready for detailed forecast cards.
- Reusable Bootstrap 5 layout with Font Awesome icons and a custom theme located in `assests/styles/style.css`.
- Geo-aware header that displays `request`-based local time using the [ipapi.co](https://ipapi.co) lookup service with graceful fallback for localhost.

## Tech Stack
- Python 3.10+
- Flask
- Bootstrap 5 / Font Awesome
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
   pip install flask requests
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

## License
This project currently has no explicit license. Add one before distributing or deploying publicly.

