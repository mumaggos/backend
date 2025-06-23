from src.database import db
from datetime import datetime

class Newsletter(db.Model):
    __tablename__ = 'newsletters'
    
    email = db.Column(db.String(100), primary_key=True)
    subscription_date = db.Column(db.DateTime, default=datetime.utcnow)
    language_preference = db.Column(db.String(2), default='pt')
    is_active = db.Column(db.Boolean, default=True)
    
    def __init__(self, email, language_preference='pt'):
        self.email = email
        self.language_preference = language_preference
        
    def to_dict(self):
        return {
            'email': self.email,
            'subscription_date': self.subscription_date.isoformat() if self.subscription_date else None,
            'language_preference': self.language_preference,
            'is_active': self.is_active
        }
