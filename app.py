import os
import threading
from app import create_app
from app.tasks import check_weather_alerts, trigger_daily_forecast_webhooks

app = create_app()

if __name__ == "__main__":
    if not os.environ.get("VERCEL"):
        # Start background threads
        # We pass 'app' to tasks so they can push app context
        alert_thread = threading.Thread(target=check_weather_alerts, args=(app,), daemon=True)
        alert_thread.start()
        
        daily_thread = threading.Thread(target=trigger_daily_forecast_webhooks, args=(app,), daemon=True)
        daily_thread.start()
        
    app.run(debug=True)