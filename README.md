
# SynoCast 🌦️

SynoCast is an advanced, AI-enhanced weather storytelling platform that provides hyper-local forecasts, climate news, and intelligent insights.

## Features ✨

*   **AI-Driven Insights**: Powered by **Google Gemini 2.0 Flash**, getting detailed safety advice, health risks, and travel packing lists.
*   **Hyper-Local Weather**: Real-time weather data from OpenWeatherMap.
*   **Smart News**: Curated weather news filtered and categorized by AI.
*   **Interactive 3D Maps**: Explore global weather patterns.
*   **Voice Assistant**: Integrated Alexa and Google Assistant support.
*   **PWA Support**: Installable on mobile and desktop.
*   **Subscription System**: Verified email alerts and push notifications.

## Project Structure 📂

```
SynoCast/
├── app/
│   ├── assets/          # Static files (CSS, JS, Images)
│   ├── routes/          # Flask Blueprints (API, Main, Auth, Subscribe)
│   ├── templates/       # HTML Templates (Jinja2)
│   ├── utils/           # Helper modules (Weather, News, Notifications...)
│   ├── database.py      # SQLite Database handling
│   ├── tasks.py         # Background tasks (Alerts)
│   └── __init__.py      # App Factory
├── subscriptions.db     # SQLite Database (Local)
├── README.md            # This file
└── ...
```

## Setup & specific instructions 🛠️

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    Create a `.env` file with the following keys:
    *   `OPENWEATHER_API_KEY`: For weather data.
    *   `GEMINI_API_KEY`: For AI features.
    *   `NEWS_API_KEY`: For global news.
    *   `RESEND_API_KEY`: For sending emails.
    *   `FLASK_SECRET_KEY`: For security.

3.  **Run Locally**:
    ```bash
    python -m flask run
    ```

## Subscription & Notifications 🔔

*   **Flow**: Users enter email -> Receive OTP via Email -> Verify OTP -> Subscribed.
*   **Database**: Users are stored in `subscriptions` table. Emails are unique.
*   **Unsubscribe**: Every email contains a one-click unsubscribe link.
*   **Alerts**: The system checks for severe weather every hour (background task) and sends emails/push notifications if criteria are met.

## Advertising 📢

*   **AdSense**: Integrated with Google AdSense.
*   **Placements**: Ad banners are dynamically placed using the `ad_banner` macro in templates.

## Contributing 🤝

1.  Fork the repository.
2.  Create a feature branch.
3.  Commit your changes.
4.  Open a Pull Request.

---
&copy; 2026 SynoCast. All rights reserved.
