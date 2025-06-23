from src.database import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    wallet_address = db.Column(db.String(42), primary_key=True)
    username = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    preferred_language = db.Column(db.String(2), default='pt')
    is_admin = db.Column(db.Boolean, default=False)
    
    def __init__(self, wallet_address, username=None, email=None, preferred_language='pt', is_admin=False):
        self.wallet_address = wallet_address
        self.username = username
        self.email = email
        self.preferred_language = preferred_language
        self.is_admin = is_admin
        
    def to_dict(self):
        return {
            'wallet_address': self.wallet_address,
            'username': self.username,
            'email': self.email,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'preferred_language': self.preferred_language,
            'is_admin': self.is_admin
        }
