from app.extensions import db
from datetime import datetime

class Subscriber(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, index=True)
    phone = db.Column(db.String(20))
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    subscription_type = db.Column(db.String(20), default='email')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Subscriber {self.email}>'

class UserPreferences(db.Model):
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, index=True)
    alert_thresholds = db.Column(db.JSON)
    notification_channels = db.Column(db.JSON)
    phone_number = db.Column(db.String(20))
    language = db.Column(db.String(5), default='en')
    timezone = db.Column(db.String(50))
    currency = db.Column(db.String(3), default='USD')
    temperature_unit = db.Column(db.String(1), default='C')
    activities = db.Column(db.JSON)
    dashboard_config = db.Column(db.JSON)
    health_config = db.Column(db.JSON)

    def __repr__(self):
        return f'<UserPreferences {self.email}>'

class FavoriteLocation(db.Model):
    __tablename__ = 'favorite_locations'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<FavoriteLocation {self.city}, {self.country}>'

class PushSubscription(db.Model):
    __tablename__ = 'push_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(500), unique=True)
    p256dh = db.Column(db.String(200))
    auth = db.Column(db.String(200))
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PushSubscription {self.id}>'
