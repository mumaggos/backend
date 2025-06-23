from src.database import db
from datetime import datetime

class Config(db.Model):
    __tablename__ = 'configs'
    
    config_id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(100), nullable=False, unique=True)
    config_value = db.Column(db.Text, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    updated_by = db.Column(db.String(42), db.ForeignKey('users.wallet_address'), nullable=True)
    
    def __init__(self, config_key, config_value, updated_by=None):
        self.config_key = config_key
        self.config_value = config_value
        self.updated_by = updated_by
        
    def to_dict(self):
        return {
            'config_id': self.config_id,
            'config_key': self.config_key,
            'config_value': self.config_value,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'updated_by': self.updated_by
        }
