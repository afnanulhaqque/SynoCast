# SynoCast

SynoCast is a lightweight Flask prototype for a weather storytelling hub. It serves a marketing-style landing page, a curated newsroom, and a weather dashboard while dynamically showing the visitor’s local date, time, and timezone based on their IP address.

**Live Preview:** [https://syno-cast.vercel.app/](https://syno-cast.vercel.app/)

## Features

- **Landing Page:** Highlights the WeatherTrip brand story with hero banners and promotional content.
- **News Page:** Showcases breaking and featured weather stories using static sample data and imagery.
- **Weather Dashboard:** Interactive weather page with real-time forecast data.
- **Interactive Map:** Features a dynamic map (Leaflet.js) integrated into the weather page for location-based updates.
- **Subscription System:** Email subscription system via Resend with OTP verification.
- **Chatbot:** A built-in chatbot interface for user interaction (currently in demo mode).
- **Responsive Design:** Reusable Bootstrap 5 layout with Font Awesome icons and a custom theme.
- **Geo-Aware Header:** Displays local time and timezone based on the user's IP address using [ipapi.co](https://ipapi.co).

## Tech Stack

- **Backend:** Python 3.10+, Flask
- **Database:** SQLite
- **Frontend:** Bootstrap 5, Vanilla CSS, Font Awesome
- **Maps:** Leaflet.js
- **Email Service:** Resend API
- **Utilities:** ipapi.co (Timezone/Location lookup)

## Project Structure

```
app.py                 # Flask app with routes and backend logic
templates/             # Jinja templates (base + page-specific)
assests/               # Static images, icons, JS, and custom CSS
  ├── js/              # JavaScript files (map, weather, modal logic)
  ├── styles/          # CSS stylesheets
  └── ...              # Images and icons
subscriptions.db       # SQLite database for storing subscriptions
```

## Getting Started

1. **Create & activate a virtual environment**

   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

2. **Install dependencies**

   ```bash
   pip install flask requests resend
   ```

3. **Run the development server**
   ```bash
   python app.py
   ```
   The site will be available at [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Customization

- **Content:** Update text and links in `templates/home.html`, `templates/news.html`, and `templates/weather.html`.
- **Styling:** Modify `assests/styles/style.css` for theme adjustments.
- **Map Logic:** Adjust map behavior in `assests/js/map.js`.

## Deployment

- This project is configured for deployment on Vercel (`vercel.json` included).
- For other platforms (Render, Railway, etc.), ensure you use a production WSGI server like Gunicorn.

## License

This project currently has no explicit license.
