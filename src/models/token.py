from src.database import db
from datetime import datetime

class Token(db.Model):
    __tablename__ = 'tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    wallet_address = db.Column(db.String(42), db.ForeignKey('users.wallet_address'), nullable=False)
    token_amount = db.Column(db.Float, default=0)
    staked_amount = db.Column(db.Float, default=0)
    staking_start_date = db.Column(db.DateTime, nullable=True)
    last_reward_date = db.Column(db.DateTime, nullable=True)
    
    def __init__(self, wallet_address, token_amount=0, staked_amount=0):
        self.wallet_address = wallet_address
        self.token_amount = token_amount
        self.staked_amount = staked_amount
        
    def to_dict(self):
        return {
            'wallet_address': self.wallet_address,
            'token_amount': self.token_amount,
            'staked_amount': self.staked_amount,
            'staking_start_date': self.staking_start_date.isoformat() if self.staking_start_date else None,
            'last_reward_date': self.last_reward_date.isoformat() if self.last_reward_date else None,
            'total_amount': self.token_amount + self.staked_amount
        }
