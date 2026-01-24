from app.extensions import db
from datetime import datetime

class WeatherIdiom(db.Model):
    __tablename__ = 'weather_idioms'
    
    id = db.Column(db.Integer, primary_key=True)
    condition = db.Column(db.String(50), nullable=False)
    idiom = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(5), nullable=False)
    meaning = db.Column(db.Text)
    cultural_context = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<WeatherIdiom {self.condition} ({self.language})>'

class CurrencyRate(db.Model):
    __tablename__ = 'currency_rates'
    
    id = db.Column(db.Integer, primary_key=True)
    base_currency = db.Column(db.String(3), nullable=False)
    target_currency = db.Column(db.String(3), nullable=False)
    rate = db.Column(db.Float, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CurrencyRate {self.base_currency}/{self.target_currency}: {self.rate}>'

class EducationalResource(db.Model):
    __tablename__ = 'educational_resources'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False) # HTML or Markdown
    category = db.Column(db.String(50))
    language = db.Column(db.String(5), default='en')
    published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<EducationalResource {self.title}>'
