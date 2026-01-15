from flask import Flask, render_template, request, jsonify
import os
from .extensions import csrf, limiter, talisman
from .database import init_db
import threading

def create_app(test_config=None):
    app = Flask(__name__, static_folder='assets', static_url_path='/assets')
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_key_123")
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    if test_config:
        app.config.update(test_config)

    # Init Extensions
    csrf.init_app(app)
    limiter.init_app(app)

    # Talisman Config
    csp = {
        'default-src': ["'self'", "https://*.googleapis.com", "https://*.google.com"],
        'script-src': ["'self'", "'unsafe-inline'", "https://*.googleapis.com", 
                       "https://*.gstatic.com", "https://*.google.com", "https://maps.googleapis.com", 
                       "https://unpkg.com", "https://cdnjs.cloudflare.com",
                       "https://cdn.jsdelivr.net", "https://*.googlesyndication.com",
                       "https://*.adtrafficquality.google", "https://*.googleadservices.com",
                       "https://html2canvas.hertzen.com"],
        'style-src': ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com", 
                      "https://unpkg.com", "https://cdnjs.cloudflare.com",
                      "https://cdn.jsdelivr.net", "https://*.google.com"],
        'img-src': ["'self'", "data:", "https://*.openweathermap.org", 
                    "https://tile.openstreetmap.org", "https://*.unsplash.com", 
                    "https://flagcdn.com", "https://*.ggpht.com",
                    "https://*.google.com", "https://*.gstatic.com",
                    "https://*.adtrafficquality.google",
                    "https://openweathermap.org", "https://www.bolnews.com", 
                    "https://www.nation.com.pk", "https://*.theatlantic.com",
                    "https://www.aljazeera.com", "https://s.yimg.com",
                    "https://i0.wp.com", "https://www.rte.ie", "https://*.wp.com"],
        'connect-src': ["'self'", "https://api.openweathermap.org", 
                        "https://nominatim.openstreetmap.org", 
                        "https://countriesnow.space",
                        "https://api.exchangerate-api.com",
                        "https://generativelanguage.googleapis.com",
                        "https://ip-api.com", "https://cdn.jsdelivr.net",
                        "https://*.google.com", "https://*.gstatic.com", "https://*.adtrafficquality.google",
                        "https://fonts.googleapis.com", "https://cdnjs.cloudflare.com",
                        "https://*.googlesyndication.com", "https://*.theatlantic.com",
                        "https://www.aljazeera.com", "https://s.yimg.com",
                        "https://i0.wp.com", "https://www.rte.ie",
                        "https://www.bolnews.com", "https://www.nation.com.pk",
                        "https://unpkg.com", "https://html2canvas.hertzen.com",
                        "https://openweathermap.org", "https://*.openweathermap.org"],
        'font-src': ["'self'", "https://fonts.gstatic.com", "https://cdnjs.cloudflare.com"],
        'frame-src': ["'self'", "https://*.google.com", "https://*.doubleclick.net", "https://*.googlesyndication.com", "https://*.adtrafficquality.google"]
    }

    if not os.environ.get("VERCEL"):
        talisman.init_app(app, content_security_policy=csp, force_https=False)
    else:
        talisman.init_app(app, content_security_policy=csp)

    # Initialize Database
    with app.app_context():
        try:
            init_db()
        except Exception as e:
            app.logger.error(f"Database initialization failed: {e}")
            
    # Upload Folder Setup
    # Note: 'assets' is now inside 'app/assets', so path should be relative to app.root_path or static_folder
    # But since we set static_folder='assets', and it's relative to app package, 
    # Flask finds it at app/assets.
    # The UPLOAD_FOLDER logic in app.py was: os.path.join('assets', 'user_uploads')
    # This relied on CWD being the project root.
    # If we run from project root, 'assets' doesn't exist anymore (it's in app/assets).
    # We should set it relative to the static folder.
    
    upload_folder = os.path.join(app.static_folder, 'user_uploads')
    # Make sure it's absolute or correct relative to CWD
    if not os.path.isabs(upload_folder):
        # app.static_folder is usually absolute if configured defaults, but here we passed 'assets'
        # So it's relative to the application package path? 
        # Actually Flask documentation says: "If x is a relative path, it is taken to be 
        # relative to the application’s root path." 
        # The application's root path is where __name__ is defined, which is app/
        pass

    # We need to ensure the uploads folder exists
    if not os.environ.get("VERCEL"):
        try:
            full_upload_path = os.path.join(app.root_path, 'assets', 'user_uploads')
            if not os.path.exists(full_upload_path):
                os.makedirs(full_upload_path)
        except Exception as e:
             app.logger.warning(f"Could not create upload folder: {e}")

    # Register Blueprints
    from .routes.main import main_bp
    from .routes.api import api_bp
    from .routes.auth import auth_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)

    # Register Error Handlers
    register_error_handlers(app)
    
    return app

def register_error_handlers(app):
    from jinja2.exceptions import TemplateSyntaxError
    from . import utils

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html", date_time_info=utils.get_local_time_string(), active_page="404"), 404

    @app.errorhandler(500)
    def internal_error(e):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Internal server error occurred"}), 500
        return render_template("500.html", date_time_info=utils.get_local_time_string(), active_page="404"), 500

    @app.errorhandler(TemplateSyntaxError)
    def syntax_error(e):
        return render_template("syntax_error.html", date_time_info=utils.get_local_time_string()), 500

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        app.logger.error(f"Unhandled Exception: {e}")
        if "Too Many Requests" in str(e) or (hasattr(e, 'code') and e.code == 429):
            if request.path.startswith('/api/'):
                return jsonify({"error": "Rate limit exceeded. Please slow down."}), 429
            return render_template("500.html", message="Too many requests. Please try again later.", date_time_info=utils.get_local_time_string(), active_page="404"), 429

        if request.path.startswith('/api/'):
            if "API_KEY_INVALID" in str(e):
                return jsonify({"error": "Invalid API Key for AI service"}), 500
            return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
        return render_template("500.html", date_time_info=utils.get_local_time_string(), active_page="404"), 500
