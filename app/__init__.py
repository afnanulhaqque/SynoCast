import os
import threading
from datetime import timedelta
from flask import Flask
from dotenv import load_dotenv

from app.extensions import csrf, limiter, talisman
from app.database import init_db
from app.routes.main import main_bp
from app.routes.api import api_bp
from app.routes.auth import auth_bp
from app.tasks import check_weather_alerts, trigger_daily_forecast_webhooks

def create_app():
    load_dotenv()
    
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="assets",
        static_url_path="/assets",
    )
    
    # Security Configuration
    app.secret_key = os.environ.get("FLASK_SECRET_KEY")
    if not app.secret_key:
        if os.environ.get("VERCEL"):
            raise ValueError("FLASK_SECRET_KEY must be set in production!")
        app.secret_key = "synocast-dev-secret-change-me"
    
    # Session Security
    app.config.update(
        SESSION_COOKIE_SECURE=True if os.environ.get("VERCEL") else False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
        MAX_CONTENT_LENGTH=5 * 1024 * 1024, # Limit uploads to 5MB
    )
    
    # Initialize Extensions
    csrf.init_app(app)
    limiter.init_app(app)
    
    # CSP Configuration
    csp = {
        'default-src': ['\'self\'', 'https://cdn.jsdelivr.net', 'https://cdnjs.cloudflare.com', 'https://*.googleapis.com', 'https://*.gstatic.com'],
        'style-src': ['\'self\'', '\'unsafe-inline\'', 'https://cdn.jsdelivr.net', 'https://fonts.googleapis.com', 'https://cdnjs.cloudflare.com', 'https://unpkg.com', 'https://*.googlesyndication.com'],
        'font-src': ['\'self\'', 'https://fonts.gstatic.com', 'https://cdnjs.cloudflare.com', 'data:'],
        'script-src': ['\'self\'', '\'unsafe-inline\'', 'https://cdn.jsdelivr.net', 'https://unpkg.com', 'https://*.googlesyndication.com', 'https://*.doubleclick.net', 'https://html2canvas.hertzen.com', 'https://cdn.plot.ly'],
        'connect-src': ['\'self\'', 'https://*'],
        'frame-src': ['\'self\'', 'https://*.doubleclick.net', 'https://*.googlesyndication.com', 'https://www.google.com'],
        'img-src': ['\'self\'', 'data:', 'https://*'],
    }
    
    talisman.init_app(
        app,
        content_security_policy=csp,
        force_https=True if os.environ.get("VERCEL") else False,
        session_cookie_secure=True if os.environ.get("VERCEL") else False,
        strict_transport_security=True,
        referrer_policy='no-referrer-when-downgrade',
        permissions_policy={
            'geolocation': '(\'self\')',
            'microphone': '()',
            'camera': '()',
        }
    )
    
    # Register Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    
    # Initialize DB
    with app.app_context():
        try:
            init_db()
        except Exception as e:
            app.logger.error(f"Database initialization failed: {e}")
            
        # Ensure upload directory exists
        UPLOAD_FOLDER = os.path.join(app.root_path, 'assets', 'user_uploads')
        if not os.environ.get("VERCEL"):
            try:
                if not os.path.exists(UPLOAD_FOLDER):
                    os.makedirs(UPLOAD_FOLDER)
            except Exception as dir_error:
                app.logger.warning(f"Could not create upload folder: {dir_error}")
                
    # Start Background Tasks (only once)
    if not os.environ.get("WERKZEUG_RUN_MAIN") == "true": # Avoid double start in debug mode
        threading.Thread(target=check_weather_alerts, args=(app.app_context(),), daemon=True).start()
        threading.Thread(target=trigger_daily_forecast_webhooks, args=(app.app_context(),), daemon=True).start()

    return app

app = create_app()
