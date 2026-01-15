# SynoCast 🌦️

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-green)
![Gemini](https://img.shields.io/badge/AI-Gemini%202.0%20Flash-magenta)
![PWA](https://img.shields.io/badge/PWA-Ready-brightgreen)
![License](https://img.shields.io/badge/License-Proprietary-red)

**SynoCast** is an intelligent, AI-first weather platform that goes beyond basic forecasting. By fusing high-precision meteorological data with **Google's Gemini 2.0 Flash** model, SynoCast transforms raw numbers into actionable narratives, travel insights, and personalized lifestyle advice.

**Live Preview:** [https://syno-cast.vercel.app/](https://syno-cast.vercel.app/)

---

## 🚀 Why SynoCast? What Makes Us Different?

Most weather apps just dump numbers on you—"25°C, 60% humidity." SynoCast is different because it **understands** the weather.

### 🧠 1. AI-Driven Storytelling, Not Just Data

Instead of static icons, SynoCast uses **Gemini 2.0 Flash** to analyze complex weather metrics in real-time. It tells you _what_ the weather means for your day:

- **"Is it safe to drive?"**: It analyzes wind, rain, and visibility to give safety ratings.
- **Health Insights**: It correlates pressure, humidity, and UV levels to warn about migraines, arthritis flare-ups, or respiratory risks.
- **Smart News**: It reads hundreds of global articles and filters out the noise, presenting only the "Critical" or "High Impact" climate stories relevant to you.

### 🌍 2. Global Context & Travel Intelligence

We don't just show you the weather in Paris; we help you **plan your trip** there:

- **Smart Packing Lists**: Generates custom packing checklists based on the specific forecast (e.g., "Bring a heavy coat, snow expected").
- **Currency & Culture**: Integrated real-time currency conversion and local weather idioms to help you blend in.
- **3D Weather Exploration**: Explore global weather patterns (wind, clouds, rain) on an interactive 3D globe.

### ⏱️ 3. Deep Historical Context

Is today unusually hot? SynoCast checks **30 years of climate comparisons** to tell you if what you're experiencing is normal or a climate anomaly.

---

## 🌟 Key Features

### 🔮 Advanced Forecasting

- **Extended Precision**: 8-day daily forecasts and 48-hour hourly breakdowns.
- **Astronomy Studio**: Track Golden Hours for photography, Moon Phases, and precise Sunrise/Sunset times.
- **Interactive Maps**: Layered visualization for clouds, precipitation, temperature, and wind speed.

### 🤖 SynoBot

- **Context-Aware Chat**: specialized AI chatbot that knows your current location's weather context. Ask it anything from "Can I BBQ tonight?" to "Explain the jet stream."

### ✈️ Travel Mode

- **Destination dashboard**: Weather, packing tips, and local insights in one view.
- **Timezone Sync**: Automatic timezone detection and adjustment.

### 📱 Progressive Web App (PWA)

- **Installable**: Works like a native app on mobile and desktop.
- **Offline Capable**: View cached forecasts even without internet.
- **Push Notifications**: Receive critical weather alerts and daily summaries.

---

## 📂 Project Structure

```
SynoCast/
├── app/                # Main application package
│   ├── __init__.py     # App factory (creates the Flask app)
│   ├── database.py     # Database connection and initialization
│   ├── utils/          # Modular helper functions (News, Climate, AI, Geo)
│   ├── routes/         # Route Blueprints (main, api, auth)
│   ├── templates/      # Jinja2 HTML templates
│   ├── assets/         # Static files (CSS, JS, Images, PWA assets)
│   └── tasks.py        # Background worker tasks
├── api/                # Vercel deployment entry points
├── scripts/            # Admin & utility scripts
├── run.py              # Local development entry point
└── requirements.txt    # Python dependencies
```

---

## 🛠️ Tech Stack

- **Backend**: Python (Flask), SQLite
- **Frontend**: HTML5, Modern CSS (Glassmorphism), JavaScript (Vanilla ES6+)
- **AI Engine**: Google Generative AI (Gemini 2.0 Flash Exp)
- **APIs & Data Sources**: OpenWeatherMap, Open-Meteo, NewsAPI, Nominatim
- **Security**: Flask-SeaSurf (CSRF), Flask-Talisman (CSP), Flask-Limiter

---

## 🏁 Getting Started

### Prerequisites

- Python 3.10 or higher
- A standard terminal or PowerShell
- API Keys for OpenWeatherMap, Google Gemini, and NewsAPI.

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

4. **Configuration (.env)**
   Create a `.env` file in the root directory. You can use the example below:

   ```env
   # Core Security
   FLASK_SECRET_KEY=your_secure_random_string_here

   # External APIs (Required)
   OPENWEATHER_API_KEY=your_owm_key
   GEMINI_API_KEY=your_google_ai_studio_key
   NEWS_API_KEY=your_newsapi_key

   # Email & Push (Optional - for alerts)
   RESEND_API_KEY=your_resend_email_key
   REPLY_TO_EMAIL=support@yourdomain.com
   VAPID_PRIVATE_KEY=your_generated_private_key
   VAPID_PUBLIC_KEY=your_generated_public_key
   ```

5. **Run the Application**
   ```bash
   python app.py
   ```
   Access the app at `http://127.0.0.1:5000`.

---

## 📡 API Reference

SynoCast exposes several internal endpoints used by the frontend:

- `GET /api/weather?lat={lat}&lon={lon}`: Current weather & forecast.
- `GET /api/weather/health?lat={lat}&lon={lon}`: AI-generated health insights.
- `GET /api/weather/extended?lat={lat}&lon={lon}`: 8-day forecast & astronomy.
- `GET /api/weather/analytics?lat={lat}&lon={lon}`: Aggregated data for charts.
- `GET /api/travel/packing-list?destination={city}`: AI-generated packing list.

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

All Rights Reserved. This software is proprietary. See `LICENSE` for more information.

<p align="center">
  Built with ❤️ and ☕ by <b>Afnanul Haqque</b>
</p>
