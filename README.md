# SynoCast 🌦️

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-green)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

**SynoCast** is a modern, lightweight weather storytelling hub built with Flask. It combines a marketing-style landing page, a curated newsroom, and an interactive weather dashboard into a seamless user experience. The application dynamically adapts to the visitor's location, displaying local time and timezone information.

**Live Preview:** [https://syno-cast.vercel.app/](https://syno-cast.vercel.app/)

---

## 🚀 Features

### 🌍 Core Experience

- **Dynamic Landing Page:** Engaging hero banners and storytelling elements that introduce the WeatherTrip brand.
- **Curated Newsroom:** A dedicated section for breaking news and featured weather stories.
- **Geo-Aware Header:** Automatically detects and displays the user's local time and timezone using IP geolocation.

### ⚡ Interactive Elements

- **Weather Dashboard:** Real-time weather forecasts with a clean, modern UI.
- **Interactive Map:** Integrated Leaflet.js map for exploring weather conditions globally.
- **Smart Chatbot:** A built-in conversational interface for instant user support (Demo).

### 🔔 Engagement

- **Subscription System:** Robust email subscription feature powered by **Resend**, complete with OTP (One-Time Password) verification for security.

---

## 🛠️ Tech Stack

- **Backend:** Python (Flask)
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5
- **Database:** SQLite
- **APIs & Services:**
  - **Resend:** Transactional emails
  - **Open-Meteo:** Weather data
  - **Nominatim (OSM):** Geocoding
  - **ipapi.co:** IP-based geolocation

---

## 📂 Project Structure

```bash
SynoCast/
├── app.py                 # Main application entry point & routes
├── subscriptions.db       # SQLite database
├── templates/             # Jinja2 HTML templates
│   ├── base.html          # Base layout with navbar & footer
│   ├── home.html          # Landing page
│   ├── news.html          # News section
│   └── weather.html       # Weather dashboard
└── assests/               # Static assets
    ├── js/                # Client-side logic (Map, Weather, Modals)
    ├── styles/            # Custom CSS
    └── ...                # Images & Icons
```

---

## 🏁 Getting Started

Follow these steps to set up the project locally.

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

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

   _(Note: If `requirements.txt` is missing, install manually: `pip install flask requests resend`)_

4. **Run the application**

   ```bash
   python app.py
   ```

5. **Visit the App**
   Open your browser and navigate to: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## ⚙️ Configuration

The application uses the following default configuration. For production, consider using environment variables.

- **Secret Key:** `synocast-dev-secret` (Change this for production!)
- **Database:** `subscriptions.db` (Auto-created on first run)
- **Resend API Key:** Configured in `app.py` (Replace with your own key for production)

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

<p align="center">
  Made with ❤️ by the SynoCast Team
</p>
