from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Newsletter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    referrer = db.Column(db.String(42), nullable=True)  # Wallet address que referiu
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'subscribed_at': self.subscribed_at.isoformat(),
            'is_active': self.is_active,
            'referrer': self.referrer
        }

class ReferralEarning(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    referrer_wallet = db.Column(db.String(42), nullable=False)
    referred_wallet = db.Column(db.String(42), nullable=False)
    amount_invested = db.Column(db.Float, nullable=False)
    commission_earned = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False)  # USDT, MATIC
    transaction_hash = db.Column(db.String(66), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_paid = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'referrer_wallet': self.referrer_wallet,
            'referred_wallet': self.referred_wallet,
            'amount_invested': self.amount_invested,
            'commission_earned': self.commission_earned,
            'currency': self.currency,
            'transaction_hash': self.transaction_hash,
            'created_at': self.created_at.isoformat(),
            'is_paid': self.is_paid
        }

class TokenPurchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wallet_address = db.Column(db.String(42), nullable=False)
    amount_invested = db.Column(db.Float, nullable=False)
    tokens_received = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False)  # USDT, MATIC
    phase = db.Column(db.Integer, nullable=False)  # 1 ou 2
    price_per_token = db.Column(db.Float, nullable=False)
    transaction_hash = db.Column(db.String(66), nullable=True)
    referrer = db.Column(db.String(42), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'wallet_address': self.wallet_address,
            'amount_invested': self.amount_invested,
            'tokens_received': self.tokens_received,
            'currency': self.currency,
            'phase': self.phase,
            'price_per_token': self.price_per_token,
            'transaction_hash': self.transaction_hash,
            'referrer': self.referrer,
            'created_at': self.created_at.isoformat()
        }

class StakingRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wallet_address = db.Column(db.String(42), nullable=False)
    amount_staked = db.Column(db.Float, nullable=False)
    staked_at = db.Column(db.DateTime, default=datetime.utcnow)
    unstaked_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    transaction_hash = db.Column(db.String(66), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'wallet_address': self.wallet_address,
            'amount_staked': self.amount_staked,
            'staked_at': self.staked_at.isoformat(),
            'unstaked_at': self.unstaked_at.isoformat() if self.unstaked_at else None,
            'is_active': self.is_active,
            'transaction_hash': self.transaction_hash
        }

class DividendPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wallet_address = db.Column(db.String(42), nullable=False)
    amount_matic = db.Column(db.Float, nullable=False)
    staked_tokens = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    transaction_hash = db.Column(db.String(66), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'wallet_address': self.wallet_address,
            'amount_matic': self.amount_matic,
            'staked_tokens': self.staked_tokens,
            'payment_date': self.payment_date.isoformat(),
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'transaction_hash': self.transaction_hash
        }

class SiteConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'key': self.key,
            'value': self.value,
            'updated_at': self.updated_at.isoformat()
        }

