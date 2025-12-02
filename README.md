# SynoCast 🌦️

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-green)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

**SynoCast** is a modern, lightweight weather storytelling hub built with Flask. It combines a marketing-style landing page with interactive weather tools to provide a seamless user experience. The application dynamically adapts to the visitor's location, displaying local time and timezone information.

**Live Preview:** [https://syno-cast.vercel.app/](https://syno-cast.vercel.app/)

---

## 🚀 Features

### 🌍 Core Experience

- **Dynamic Landing Page:** Engaging hero banners and storytelling elements that introduce the SynoCast brand.
- **Geo-Aware Header:** Automatically detects and displays the user's local time and timezone using IP geolocation.

### ⚡ Interactive Elements

- **AI Weather Assistant:** A built-in conversational interface powered by **Groq** (Cloud) and **Ollama** (Local) for instant weather-related support.
- **Interactive Map:** Integrated Leaflet.js map with backend proxy endpoints for forward and reverse geocoding (Nominatim).

### 🔔 Engagement

- **Secure Subscriptions:** Robust email subscription feature powered by **Resend**, complete with OTP (One-Time Password) verification for security.

---

## 🛠️ Tech Stack

- **Backend:** Python (Flask)
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5
- **Database:** SQLite
- **APIs & Services:**
  - **Resend:** Transactional emails
  - **Groq & Ollama:** AI Chat capabilities
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
│   ├── news.html          # News section template
│   └── weather.html       # Weather dashboard template
└── assests/               # Static assets
    ├── js/                # Client-side logic (Map, Chatbot, Modals)
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

4. **Set up Environment Variables**

   Create a `.env` file (optional for local dev, but recommended for keys):

   ```env
   GROQ_API_KEY=your_groq_api_key
   ```

5. **Run the application**

   ```bash
   python app.py
   ```

6. **Visit the App**
   Open your browser and navigate to: [http://127.0.0.1:5000](http://127.0.0.1:5000)

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
