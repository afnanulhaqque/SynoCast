# SynoCast 🌦️

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-green)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)
![AI](https://img.shields.io/badge/AI-Gemini-orange)

**SynoCast** is a sophisticated, AI-enhanced weather storytelling platform. It transforms standard meteorological data into engaging, context-aware insights, providing users with not just the forecast, but a narrative of how the weather affects their world.

**Live Preview:** [https://syno-cast.vercel.app/](https://syno-cast.vercel.app/)

---

## 🌟 Key Features

### 🌍 Intelligent Weather Ecosystem

- **Hyper-Local Context:** Automatically detects location via IP and browser sensors to provide instant local time and weather.
- **Real-Time Data:** High-fidelity current conditions and 5-day forecasts via **OpenWeatherMap**.
- **SynoBot AI Assistant:** An integrated chatbot powered by **Google Gemini 1.5 Flash** that answers weather queries using your current live context.

### 📰 AI-Curated News Feed

- **Smart Categorization:** Uses AI to filter, prioritize, and categorize global weather news into segments like "Severe Weather Alerts" and "Climate Events."
- **Urgency Awareness:** Articles are tagged with urgency levels (Critical, High, Medium, Low) to help users focus on what matters.

### 🔒 Security & Reliability

- **Enterprise-Grade Security:** Implemented with **Flask-Talisman** (CSP), **Flask-SeaSurf** (CSRF Protection), and **Flask-Limiter** (Rate Limiting).
- **OTP Verification:** Secure subscription system using **Resend API** for one-time password verification.
- **Robust Fallbacks:** High-quality dummy data and caching mechanisms ensure the UI remains functional even when upstream APIs are throttled.

---

## 🛠️ Tech Stack

- **Backend:** Python (Flask)
- **Frontend:** HTML5, Modern CSS (Glassmorphism), JavaScript (Vanilla), Bootstrap 5, Leaflet.js
- **Database:** SQLite (Subscription & Data Management)
- **AI Engine:** Google Generative AI (Gemini 1.5 Flash)
- **API integrations:**
  - **Weather:** OpenWeatherMap API
  - **News:** NewsAPI.org
  - **Email/OTP:** Resend API
  - **Geocoding:** Nominatim (OSM), ipapi.co

---

## 🏁 Getting Started

### Prerequisites

- Python 3.10 or higher
- A standard terminal or PowerShell (Windows).

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
   Create a `.env` file in the root directory and populate it with your keys:

   ```env
   FLASK_SECRET_KEY=your_random_secret_string
   GEMINI_API_KEY=your_google_gemini_api_key
   OPENWEATHER_API_KEY=your_openweather_api_key
   NEWS_API_KEY=your_news_api_key
   RESEND_API_KEY=your_resend_api_key
   REPLY_TO_EMAIL=your_support_email@example.com
   ```

5. **Initialize & Run**
   ```bash
   # The database initializes automatically on first run
   python app.py
   ```
   The application will be accessible at `http://127.0.0.1:5000`.

### 🧪 Testing & Validation

Before starting the server, you can verify your API keys using the provided test scripts:

- **Gemini:** `python test_gemini.py`
- **NewsAPI:** `python test_news_api.py`
- **Endpoints:** `python test_endpoint.py`

---

## 📡 API Documentation

SynoCast provides several internal endpoints for dynamic frontend interaction:

### `GET /api/weather`

Proxies OpenWeatherMap data with caching.

- **Params:** `lat` (float), `lon` (float)
- **Returns:** JSON containing current, forecast, and pollution data.

### `POST /api/ai_chat`

Interactive AI dialogue with weather context.

- **Payload:** `{ "message": "user text", "lat": float, "lon": float }`
- **Returns:** `{ "reply": "AI generated response" }`

### `GET /api/ip-location`

Detects approximate location based on the caller's IP.

- **Returns:** City, Country, Lat/Lon details.

### `POST /otp`

Handles subscription logic and OTP dispatch.

- **Params:** `action` (request/verify), `email` (string), `otp` (string)

---

## 📂 Project Organization

```text
SynoCast/
├── app.py              # Main application entry & route definitions
├── utils.py            # Core logic: AI categorization, API fetching, Time helpers
├── subscriptions.db    # SQLite database for storing user subscriptions
├── requirements.txt    # List of Python dependencies
├── vercel.json         # Deployment configuration for Vercel
├── templates/          # Jinja2 HTML templates
│   ├── base.html       # Shared layout and navigation
│   ├── home.html       # Dashboard with latest news
│   ├── weather.html    # Detailed interactive weather page
│   └── chat.html       # Dedicated AI chat interface (if applicable)
└── assets/             # Static assets
    ├── js/             # Modular JS (location_handler.js, weather.js, etc.)
    ├── styles/         # Premium CSS with custom design system
    └── images/         # High-resolution UI assets
```

---

## 🛠️ Configuration & Environment

| Variable              | Description                              | Source                                           |
| :-------------------- | :--------------------------------------- | :----------------------------------------------- |
| `FLASK_SECRET_KEY`    | Used for session signing and security.   | Any random string                                |
| `GEMINI_API_KEY`      | Powers SynoBot and News Categorization.  | [Google AI Studio](https://aistudio.google.com/) |
| `OPENWEATHER_API_KEY` | Provides real-time meteorological data.  | [OpenWeatherMap](https://openweathermap.org/api) |
| `NEWS_API_KEY`        | Sources global weather articles.         | [NewsAPI.org](https://newsapi.org/)              |
| `RESEND_API_KEY`      | Dispatches OTP emails for subscriptions. | [Resend.com](https://resend.com/)                |

---

## 📦 Dependencies

The project relies on the following core Python packages:

- `Flask`: Web framework
- `requests`: HTTP library for API calls
- `resend`: Email delivery service
- `google-generativeai`: Gemini AI integration
- `python-dotenv`: Environment variable management
- `flask-talisman`: Security headers & CSP
- `flask-limiter`: Rate limiting
- `flask-seasurf`: CSRF protection

---

## 🤝 Contributing

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## ⚠️ Troubleshooting

- **API Limits:** If news or weather doesn't load, check if you've exceeded the free tier limits of NewsAPI or OpenWeatherMap.
- **Missing .env:** Ensure `.env` is in the root directory. The app will log errors if keys are missing.
- **Database Errors:** If `subscriptions.db` is corrupted, delete it; the app will recreate a fresh one on the next startup.
- **Vercel Deployment:** This project is pre-configured for Vercel with `vercel.json`. Ensure the database path is set to `/tmp/` in production.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

<p align="center">
  Built with Precision by <b>Afnanul Haqque</b><br>
  <i>Empowering users with intelligent weather narratives.</i>
</p>
