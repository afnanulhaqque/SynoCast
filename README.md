# SynoCast 🌦️

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-green)
![Gemini](https://img.shields.io/badge/AI-Gemini%202.0%20Flash-magenta)
![PWA](https://img.shields.io/badge/PWA-Ready-brightgreen)
![License](https://img.shields.io/badge/License-MIT-yellow)

**SynoCast** is an intelligent, AI-first weather platform that goes beyond basic forecasting. By fusing high-precision meteorological data with **Google's Gemini 2.0 Flash** model, SynoCast transforms raw numbers into actionable narratives, travel insights, and personalized lifestyle advice.

**Live Preview:** [https://syno-cast.vercel.app/](https://syno-cast.vercel.app/)

---

## 🌟 Key Features

### 🧠 AI-Powered Insights (SynoBot)

- **Context-Aware Chat:** Ask "What should I wear for my evening run?" or "Is it safe to drive to the coast?" and get answers based on real-time weather conditions.
- **Smart News Delivery:** We analyze hundreds of global articles to filter out noise, categorizing news into "Severe Alerts," "Climate Events," and "Impact Stories" with an AI-assigned urgency score.
- **Crisis Advice:** When severe weather strikes, the AI generates specific, actionable safety advice for your exact location.

### 🔮 Advanced Forecasting

- **Extended Precision:** 8-day daily forecasts and 48-hour hourly breakdowns.
- **Astronomy Studio:** Track Golden Hours for photography, Moon Phases, and precise Sunrise/Sunset times.
- **Climate Context:** Compare today's weather with 30-year climate normals to see if it's unseasonably hot or cold (powered by Open-Meteo).
- **Interactive Maps:** Layered visualization for clouds, precipitation, temperature, and wind speed.

### ✈️ Global Travel Mode

- **Currency Intelligence:** Real-time exchange rates integrated with travel weather planning.
- **Cultural Wisdom:** Discover local weather idioms and sayings relevant to the current conditions and language.
- **Timezone Sync:** Automatic timezone detection and adjustment for any location worldwide.

### 👤 User & Community

- **Personalized Dashboard:** Customize your experience with preferred units, activity interests (hiking, photography, etc.), and alert thresholds.
- **Location Bookmarks:** Save and manage favorite locations for quick access.
- **Crowdsourced Reports:** Contribute to community weather accuracy by verifying conditions on the ground.
- **Smart Alerts:** Subscribe to email or push notifications for specific triggers (Rain, Temperature spikes, Air Quality).

### 📱 Progressive Web App (PWA)

- **Offline Capable:** View cached forecasts and basic data even without an internet connection.
- **Installable:** Add to your home screen for a native app-like experience on mobile and desktop.
- **Background Sync:** Keep data fresh with periodic background synchronization (supported browsers only).

---

## 🛠️ Tech Stack

- **Backend:** Python (Flask), SQLite
- **Frontend:** HTML5, Modern CSS (Glassmorphism), JavaScript (Vanilla ES6+)
- **AI Engine:** Google Generative AI (Gemini 2.0 Flash Exp)
- **APIs & Data Sources:**
  - **Weather:** OpenWeatherMap (One Call 3.0 & Standard), Open-Meteo (Historical/Climate)
  - **News:** NewsAPI.org
  - **Geocoding:** Nominatim (OSM), ipapi.co
  - **Communication:** Resend (Email), PyWebPush (Push Notifications)
- **Security:** Flask-SeaSurf (CSRF), Flask-Talisman (CSP), Flask-Limiter

---

## 🏁 Getting Started

### Prerequisites

- Python 3.10 or higher
- A standard terminal or PowerShell

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/afnanulhaqque/SynoCast.git
   cd SynoCast
   ```

2. **Environment Setup**

   ```bash
   python -m venv .venv

   # Windows
   .venv\Scripts\activate

   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configuration**
   Create a `.env` file in the root directory:

   ```env
   # Core
   FLASK_SECRET_KEY=your_secure_random_string

   # APIs
   OPENWEATHER_API_KEY=your_owm_key
   GEMINI_API_KEY=your_google_ai_studio_key
   NEWS_API_KEY=your_newsapi_key

   # Email & Push
   RESEND_API_KEY=your_resend_key
   REPLY_TO_EMAIL=support@yourdomain.com
   VAPID_PRIVATE_KEY=your_generated_private_key
   VAPID_PUBLIC_KEY=your_generated_public_key
   ```

   > **Note:** VAPID keys are required for Push Notifications. You can generate them using `pywebpush`.

5. **Run the Application**
   ```bash
   python app.py
   ```
   Access at `http://127.0.0.1:5000`.

---

## 📡 API Reference

SynoCast exposes several internal endpoints used by the frontend:

### Weather & Data

- `GET /api/weather?lat={lat}&lon={lon}` - Current, 5-day forecast, and pollution data.
- `GET /api/weather/extended?lat={lat}&lon={lon}` - 8-day daily, 48-hour hourly, and astronomy data.
- `GET /api/weather/history?lat={lat}&lon={lon}` - Historical weather trends.
- `GET /api/weather/analytics?lat={lat}&lon={lon}` - Aggregated data for charts.

### AI & Intelligence

- `POST /api/ai_chat` - Send a message to SynoBot with location context.
- `GET /api/idioms` - Get weather-related cultural sayings.

### Utilities

- `GET /api/geocode/search?q={query}` - Forward geocoding.
- `GET /api/geocode/reverse?lat={lat}&lon={lon}` - Reverse geocoding.
- `GET /api/currency/rates` - Latest exchange rates.

---

## ⚠️ Troubleshooting

- **One Call API Errors:** The "Extended" forecast relies on OpenWeatherMap's One Call 3.0 subscription. If you are on a free tier, the app automatically falls back to a simulated mode using standard forecast data.
- **Database Locks:** SQLite handles local concurrency well but may lock during heavy write operations. Ensure no other tool is holding the DB open.
- **Offline Mode:** Requires HTTPS (or localhost) for Service Workers to register.

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the project.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes.
4. Push to the branch.
5. Open a Pull Request.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

<p align="center">
  Built with ❤️ and ☕ by <b>Afnanul Haqque</b>
</p>
