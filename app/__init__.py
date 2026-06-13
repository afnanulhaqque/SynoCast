import os
import threading
from datetime import timedelta
from flask import Flask
from dotenv import load_dotenv

from app.extensions import csrf, limiter, talisman, db, migrate, babel
from app.database import init_db
from app.blueprints.main import main_bp
from app.blueprints.api import api_bp
from app.blueprints.auth import auth_bp
from app.blueprints.subscribe import subscribe_bp
from app.blueprints.admin import admin_bp
from app.tasks import check_weather_alerts, trigger_daily_forecast_webhooks

def create_app():
    load_dotenv()
    
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="assets",
        static_url_path="/assets",
    )
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
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
    
    # Database Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL") or "sqlite:///" + os.path.join(app.root_path, "subscriptions.db")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    def get_locale():
        # Check if user has stored preference
        # return request.accept_languages.best_match(['en', 'ur', 'ar'])
        return 'en' # Defaulting to en for now until translation files are ready

    # Initialize Extensions
    csrf.init_app(app)
    limiter.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    babel.init_app(app, locale_selector=get_locale)
    
    # Content Security Policy Configuration
    csp = {
        'default-src': ['\'self\'', 'https://cdn.jsdelivr.net', 'https://cdnjs.cloudflare.com', 'https://*.googleapis.com', 'https://*.gstatic.com'],
        'style-src': ['\'self\'', '\'unsafe-inline\'', 'https://cdn.jsdelivr.net', 'https://fonts.googleapis.com', 'https://cdnjs.cloudflare.com', 'https://unpkg.com', 'https://*.googlesyndication.com'],
        'font-src': ['\'self\'', 'https://fonts.gstatic.com', 'https://cdnjs.cloudflare.com', 'data:'],
        'script-src': ['\'self\'', '\'unsafe-inline\'', 'https://cdn.jsdelivr.net', 'https://unpkg.com', 'https://*.googlesyndication.com', 'https://*.doubleclick.net', 'https://html2canvas.hertzen.com', 'https://cdn.plot.ly', 'https://cdnjs.cloudflare.com', 'https://*.google.com', 'https://*.adtrafficquality.google', 'https://www.googletagmanager.com'],
        'connect-src': ['\'self\'', 'https://*', 'https://ep2.adtrafficquality.google'],
        'frame-src': ['\'self\'', 'https://*.doubleclick.net', 'https://*.googlesyndication.com', 'https://www.google.com', 'https://*.adtrafficquality.google'],
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
            'geolocation': 'self',
            'microphone': 'self',
            'camera': '()',
        }
    )
    
    # Register Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(subscribe_bp)
    app.register_blueprint(admin_bp)
    
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
