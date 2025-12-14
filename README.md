# SynoCast 🌦️

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-green)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

**SynoCast** is a modern, feature-rich weather forecasting application built with Flask. It combines real-time weather data with AI-powered insights, news updates, and a responsive design to deliver a premium user experience. The application automatically adapts to the user's location and provides detailed forecasts, weather news, and an interactive AI assistant.

**Live Preview:** [https://syno-cast.vercel.app/](https://syno-cast.vercel.app/)

---

## 🚀 Features

### 🌍 Core Weather Experience

- **Real-Time Data:** Accurate current weather and forecasts powered by the **OpenWeatherMap API**.
- **Detailed Forecasts:** 5-day / 3-hour forecast data with visual trends.
- **Geo-Awareness:** Automatically detects and displays local time, city, and region using IP geolocation (ipapi.co).

### 🤖 SynoBot - AI Weather Assistant

- **Smart Conversations:** Integrated AI chatbot ("SynoBot") to answer weather-related queries.
- **Dual-Engine Power:**
  - **Cloud:** Powered by **Groq** (Llama 3 model) for fast, deployed responses.
  - **Local:** Fallback to **Ollama** (Llama 3 model) for local development and privacy.

### ⚡ Interactive & Dynamic

- **Interactive Map:** Leaflet.js map with search capabilities, ensuring users can find weather for any specific location.
- **News Integration:** A dedicated News section aggregating the latest weather and environmental stories.
- **Responsive Design:** Fully optimized for Mobile, Tablet, and Desktop with adaptive layouts (e.g., specific mobile adjustments for navigation and modals).

### 🔔 User Engagement

- **Secure Subscriptions:** Email subscription system with **OTP (One-Time Password)** verification using the **Resend API**.
- **User-Friendly Forms:** Clean and secure input handling for user data.

### 🛡️ Robustness

- **Custom Error Pages:** Polished, branded pages for 404 (Not Found) and 500 (Server Error) to maintain user immersion even when things go wrong.
- **Security:** Secure session handling and environment-based configuration.

---

## 🛠️ Tech Stack

- **Backend:** Python (Flask)
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5
- **Database:** SQLite (for subscription management)
- **AI & ML:** Groq API (Cloud), Ollama (Local)
- **APIs & Services:**
  - **OpenWeatherMap:** Weather data
  - **Resend:** Transactional emails & OTPs
  - **Nominatim (OSM):** Geocoding (Forward & Reverse)
  - **ipapi.co:** IP geolocation

---

## 📂 Project Structure

```bash
SynoCast/
├── app.py                 # Main Flask application & routes
├── subscriptions.db       # SQLite database (auto-created)
├── templates/             # Jinja2 HTML templates
│   ├── base.html          # Master layout
│   ├── home.html          # Main dashboard
│   ├── weather.html       # Detailed weather view
│   ├── news.html          # Weather news feed
│   ├── 404.html           # Custom 404 error page
│   └── ...                # Other templates
├── assests/               # Static assets
│   ├── js/                # Client-side scripts (Map, Chat, UI)
│   ├── styles/            # Custom CSS
│   └── icons/             # Images & WebP assets
└── requirements.txt       # Python dependencies
```

---

## 🏁 Getting Started

Follow these steps to run SynoCast locally.

### Prerequisites

- Python 3.10 or higher
- [Ollama](https://ollama.com/) (Optional, for local AI chat)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/synocast.git
   cd synocast
   ```

2. **Create a virtual environment**

   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Environment Variables**

   Create a `.env` file in the root directory. While some keys can be configured in `app.py`, it is recommended to use environment variables for security, especially for the AI features:

   ```env
   GROQ_API_KEY=your_groq_api_key_here
   # Add other keys if you modify app.py to read them from env:
   # RESEND_API_KEY=...
   # OPENWEATHER_API_KEY=...
   ```

5. **Run the application**

   ```bash
   python app.py
   ```

6. **Visit the App**
   Open your browser and navigate to: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is available under the [MIT License](LICENSE).

---

<p align="center">
  Made with ❤️ by the SynoCast Team
</p>
