import os
import sqlite3
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Determine database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if os.environ.get("VERCEL"):
    DATABASE = "/tmp/subscriptions.db"
else:
    DATABASE = os.path.join(BASE_DIR, "..", "subscriptions.db")

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Create the subscriptions and preferences tables if they do not already exist."""
    with get_db() as conn:
        try:
            # Subscriptions table with location support
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    phone TEXT,
                    lat REAL,
                    lon REAL,
                    subscription_type TEXT DEFAULT 'email',
                    created_at TEXT NOT NULL
                )
                """
            )
            
            # User preferences for alerts and global settings
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE,
                    alert_thresholds TEXT, -- JSON string
                    notification_channels TEXT, -- JSON string
                    phone_number TEXT,
                    language TEXT DEFAULT 'en',
                    timezone TEXT,
                    currency TEXT DEFAULT 'USD'
                )
                """
            )
            
            # Push Subscriptions
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS push_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint TEXT UNIQUE,
                    p256dh TEXT,
                    auth TEXT,
                    lat REAL,
                    lon REAL,
                    created_at TEXT
                )
                """
            )
            
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(subscriptions)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if "phone" not in columns:
                conn.execute("ALTER TABLE subscriptions ADD COLUMN phone TEXT")
            if "subscription_type" not in columns:
                conn.execute("ALTER TABLE subscriptions ADD COLUMN subscription_type TEXT DEFAULT 'email'")
            if "lat" not in columns:
                conn.execute("ALTER TABLE subscriptions ADD COLUMN lat REAL")
            if "lon" not in columns:
                conn.execute("ALTER TABLE subscriptions ADD COLUMN lon REAL")
                
            conn.commit()
            
            # Favorite Locations Table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS favorite_locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    lat REAL,
                    lon REAL,
                    city TEXT,
                    country TEXT,
                    created_at TEXT
                )
                """
            )

            # Check user_preferences columns
            cursor.execute("PRAGMA table_info(user_preferences)")
            up_columns = [column[1] for column in cursor.fetchall()]
            
            if "temperature_unit" not in up_columns:
                conn.execute("ALTER TABLE user_preferences ADD COLUMN temperature_unit TEXT DEFAULT 'C'")
            if "activities" not in up_columns:
                conn.execute("ALTER TABLE user_preferences ADD COLUMN activities TEXT")
            if "dashboard_config" not in up_columns:
                conn.execute("ALTER TABLE user_preferences ADD COLUMN dashboard_config TEXT")
            if "health_config" not in up_columns:
                conn.execute("ALTER TABLE user_preferences ADD COLUMN health_config TEXT")
            if "language" not in up_columns:
                conn.execute("ALTER TABLE user_preferences ADD COLUMN language TEXT DEFAULT 'en'")
            if "timezone" not in up_columns:
                conn.execute("ALTER TABLE user_preferences ADD COLUMN timezone TEXT")
            if "currency" not in up_columns:
                conn.execute("ALTER TABLE user_preferences ADD COLUMN currency TEXT DEFAULT 'USD'")

            # Weather Idioms Table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS weather_idioms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    condition TEXT NOT NULL,
                    idiom TEXT NOT NULL,
                    language TEXT NOT NULL,
                    meaning TEXT,
                    cultural_context TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )

            # Currency Rates Table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS currency_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    base_currency TEXT NOT NULL,
                    target_currency TEXT NOT NULL,
                    rate REAL NOT NULL,
                    last_updated TEXT NOT NULL
                )
                """
            )

            conn.commit()
                
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            # Re-raise or handle? For now just log. 
            print(f"Database initialization error: {e}")
