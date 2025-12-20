# SynoCast 🌦️

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-green)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

**SynoCast** is a modern, feature-rich weather forecasting application built with Flask. It combines real-time weather data with AI-powered insights, news updates, and a responsive design to deliver a premium user experience.

**Live Preview:** [https://syno-cast.vercel.app/](https://syno-cast.vercel.app/)

---

## 🚀 Features

### 🌍 Core Weather Experience

- **Real-Time Data:** Accurate current weather and forecasts powered by the **OpenWeatherMap API**.
- **Detailed Forecasts:** 5-day / 3-hour forecast data with visual trends.
- **Geo-Awareness:** Automatically detects and displays local time, city, and region using IP geolocation.

### 🤖 SynoBot - AI Weather Assistant

- **Google Gemini Integration:** Powered by **Google Gemini 2.5 Flash** for intelligent, context-aware weather conversations.
- **Location Context:** Automatically uses the user's current weather conditions to provide personalized advice.

### ⚡ Interactive & Dynamic

- **Interactive Map:** Leaflet.js map with search capabilities and reverse geocoding.
- **News Integration:** Dedicated section for the latest weather and climate change stories.
- **Responsive Design:** Fully optimized for Mobile, Tablet, and Desktop with a single consolidated stylesheet.

### 🔔 User Engagement

- **Secure Subscriptions:** Email subscription system with **OTP (One-Time Password)** verification via **Resend API**.

---

## 🛠️ Tech Stack

- **Backend:** Python (Flask)
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla), Bootstrap 5
- **Database:** SQLite (Subscription management)
- **AI Service:** Google Gemini API
- **APIs:** OpenWeatherMap, Resend, Nominatim (OSM), ipapi.co

---

## 📂 Project Structure

```bash
SynoCast/
├── app.py                 # Main Flask application & routes
├── subscriptions.db       # SQLite database (auto-created)
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (API keys)
├── templates/             # Jinja2 HTML templates
│   ├── base.html          # Master layout
│   ├── home.html          # Home dashboard
│   ├── weather.html       # Detailed weather view
│   ├── news.html          # News feed
│   └── ...                # Error & auxiliary pages
└── assests/               # Static assets (Images, JS, CSS)
    ├── js/                # Component-specific logic
    ├── styles/            # Consolidated style.css
    └── icons/             # UI icons
```

---

## 🏁 Getting Started

### Prerequisites

- Python 3.10 or higher
- API Keys for Gemini, OpenWeatherMap, and Resend.

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/synocast.git
   cd synocast
   ```

2. **Set up Virtual Environment**

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
   Create a `.env` file in the root:

   ```env
   FLASK_SECRET_KEY=your_secret_key
   GEMINI_API_KEY=your_gemini_key
   OPENWEATHER_API_KEY=your_owm_key
   RESEND_API_KEY=your_resend_key
   ```

5. **Run**
   ```bash
   python app.py
   ```

---

## 📄 License

This project is licensed under the MIT License.

---

<p align="center">Made with ❤️ by the SynoCast Team</p>
