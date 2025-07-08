from flask import Blueprint, request, jsonify
from src.models.casinofound import db, Newsletter, ReferralEarning, TokenPurchase, StakingRecord, DividendPayment, SiteConfig
from datetime import datetime
import re

casinofound_bp = Blueprint('casinofound', __name__)

# Validação de email
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Validação de endereço Ethereum
def is_valid_wallet(address):
    pattern = r'^0x[a-fA-F0-9]{40}$'
    return re.match(pattern, address) is not None

# Newsletter Routes
@casinofound_bp.route('/newsletter/subscribe', methods=['POST'])
def subscribe_newsletter():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        referrer = data.get('referrer', '').strip()
        
        if not email or not is_valid_email(email):
            return jsonify({'error': 'Email inválido'}), 400
        
        # Verificar se já existe
        existing = Newsletter.query.filter_by(email=email).first()
        if existing:
            if existing.is_active:
                return jsonify({'message': 'Email já subscrito'}), 200
            else:
                # Reativar subscrição
                existing.is_active = True
                existing.subscribed_at = datetime.utcnow()
                db.session.commit()
                return jsonify({'message': 'Subscrição reativada com sucesso'}), 200
        
        # Validar referrer se fornecido
        if referrer and not is_valid_wallet(referrer):
            referrer = None
        
        # Criar nova subscrição
        newsletter = Newsletter(
            email=email,
            referrer=referrer
        )
        
        db.session.add(newsletter)
        db.session.commit()
        
        return jsonify({'message': 'Subscrito com sucesso'}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@casinofound_bp.route('/newsletter/unsubscribe', methods=['POST'])
def unsubscribe_newsletter():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email or not is_valid_email(email):
            return jsonify({'error': 'Email inválido'}), 400
        
        newsletter = Newsletter.query.filter_by(email=email).first()
        if not newsletter:
            return jsonify({'error': 'Email não encontrado'}), 404
        
        newsletter.is_active = False
        db.session.commit()
        
        return jsonify({'message': 'Subscrição cancelada com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@casinofound_bp.route('/newsletter/list', methods=['GET'])
def get_newsletter_list():
    try:
        # Verificar autorização (simplificado)
        auth_header = request.headers.get('Authorization')
        if not auth_header or auth_header != 'Bearer admin-token':
            return jsonify({'error': 'Não autorizado'}), 401
        
        newsletters = Newsletter.query.filter_by(is_active=True).all()
        return jsonify({
            'newsletters': [n.to_dict() for n in newsletters],
            'total': len(newsletters)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

# Referral Routes
@casinofound_bp.route('/referral/earnings/<wallet_address>', methods=['GET'])
def get_referral_earnings(wallet_address):
    try:
        if not is_valid_wallet(wallet_address):
            return jsonify({'error': 'Endereço de carteira inválido'}), 400
        
        earnings = ReferralEarning.query.filter_by(referrer_wallet=wallet_address.lower()).all()
        
        total_earned = sum(e.commission_earned for e in earnings)
        pending_earnings = sum(e.commission_earned for e in earnings if not e.is_paid)
        total_referrals = len(set(e.referred_wallet for e in earnings))
        
        return jsonify({
            'total_earned': total_earned,
            'pending_earnings': pending_earnings,
            'total_referrals': total_referrals,
            'earnings': [e.to_dict() for e in earnings]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@casinofound_bp.route('/referral/record', methods=['POST'])
def record_referral_earning():
    try:
        data = request.get_json()
        
        referrer_wallet = data.get('referrer_wallet', '').strip().lower()
        referred_wallet = data.get('referred_wallet', '').strip().lower()
        amount_invested = float(data.get('amount_invested', 0))
        currency = data.get('currency', '').upper()
        transaction_hash = data.get('transaction_hash', '').strip()
        
        if not is_valid_wallet(referrer_wallet) or not is_valid_wallet(referred_wallet):
            return jsonify({'error': 'Endereços de carteira inválidos'}), 400
        
        if amount_invested <= 0:
            return jsonify({'error': 'Valor investido deve ser maior que zero'}), 400
        
        if currency not in ['USDT', 'MATIC']:
            return jsonify({'error': 'Moeda inválida'}), 400
        
        # Calcular comissão (5%)
        commission_earned = amount_invested * 0.05
        
        # Registar ganho de referral
        earning = ReferralEarning(
            referrer_wallet=referrer_wallet,
            referred_wallet=referred_wallet,
            amount_invested=amount_invested,
            commission_earned=commission_earned,
            currency=currency,
            transaction_hash=transaction_hash
        )
        
        db.session.add(earning)
        db.session.commit()
        
        return jsonify({
            'message': 'Ganho de referral registado com sucesso',
            'commission_earned': commission_earned
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

# Token Purchase Routes
@casinofound_bp.route('/purchase/record', methods=['POST'])
def record_token_purchase():
    try:
        data = request.get_json()
        
        wallet_address = data.get('wallet_address', '').strip().lower()
        amount_invested = float(data.get('amount_invested', 0))
        tokens_received = float(data.get('tokens_received', 0))
        currency = data.get('currency', '').upper()
        phase = int(data.get('phase', 1))
        price_per_token = float(data.get('price_per_token', 0))
        transaction_hash = data.get('transaction_hash', '').strip()
        referrer = data.get('referrer', '').strip().lower() if data.get('referrer') else None
        
        if not is_valid_wallet(wallet_address):
            return jsonify({'error': 'Endereço de carteira inválido'}), 400
        
        if referrer and not is_valid_wallet(referrer):
            return jsonify({'error': 'Endereço de referrer inválido'}), 400
        
        # Registar compra
        purchase = TokenPurchase(
            wallet_address=wallet_address,
            amount_invested=amount_invested,
            tokens_received=tokens_received,
            currency=currency,
            phase=phase,
            price_per_token=price_per_token,
            transaction_hash=transaction_hash,
            referrer=referrer
        )
        
        db.session.add(purchase)
        
        # Se há referrer, registar ganho de referral
        if referrer:
            commission = amount_invested * 0.05
            earning = ReferralEarning(
                referrer_wallet=referrer,
                referred_wallet=wallet_address,
                amount_invested=amount_invested,
                commission_earned=commission,
                currency=currency,
                transaction_hash=transaction_hash
            )
            db.session.add(earning)
        
        db.session.commit()
        
        return jsonify({'message': 'Compra registada com sucesso'}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@casinofound_bp.route('/purchase/stats', methods=['GET'])
def get_purchase_stats():
    try:
        # Estatísticas gerais
        total_purchases = TokenPurchase.query.count()
        total_invested = db.session.query(db.func.sum(TokenPurchase.amount_invested)).scalar() or 0
        total_tokens_sold = db.session.query(db.func.sum(TokenPurchase.tokens_received)).scalar() or 0
        
        # Estatísticas por fase
        phase1_sold = db.session.query(db.func.sum(TokenPurchase.tokens_received)).filter_by(phase=1).scalar() or 0
        phase2_sold = db.session.query(db.func.sum(TokenPurchase.tokens_received)).filter_by(phase=2).scalar() or 0
        
        return jsonify({
            'total_purchases': total_purchases,
            'total_invested': total_invested,
            'total_tokens_sold': total_tokens_sold,
            'phase1_sold': phase1_sold,
            'phase2_sold': phase2_sold
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

# Staking Routes
@casinofound_bp.route('/staking/record', methods=['POST'])
def record_staking():
    try:
        data = request.get_json()
        
        wallet_address = data.get('wallet_address', '').strip().lower()
        amount_staked = float(data.get('amount_staked', 0))
        transaction_hash = data.get('transaction_hash', '').strip()
        
        if not is_valid_wallet(wallet_address):
            return jsonify({'error': 'Endereço de carteira inválido'}), 400
        
        if amount_staked < 100:
            return jsonify({'error': 'Quantidade mínima para staking é 100 CFD'}), 400
        
        # Registar staking
        staking = StakingRecord(
            wallet_address=wallet_address,
            amount_staked=amount_staked,
            transaction_hash=transaction_hash
        )
        
        db.session.add(staking)
        db.session.commit()
        
        return jsonify({'message': 'Staking registado com sucesso'}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@casinofound_bp.route('/staking/balance/<wallet_address>', methods=['GET'])
def get_staking_balance(wallet_address):
    try:
        if not is_valid_wallet(wallet_address):
            return jsonify({'error': 'Endereço de carteira inválido'}), 400
        
        # Calcular saldo em staking
        staked = db.session.query(db.func.sum(StakingRecord.amount_staked)).filter_by(
            wallet_address=wallet_address.lower(),
            is_active=True
        ).scalar() or 0
        
        # Buscar registos de staking ativos
        records = StakingRecord.query.filter_by(
            wallet_address=wallet_address.lower(),
            is_active=True
        ).all()
        
        return jsonify({
            'total_staked': staked,
            'records': [r.to_dict() for r in records]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

# Configuration Routes
@casinofound_bp.route('/config/<key>', methods=['GET'])
def get_config(key):
    try:
        config = SiteConfig.query.filter_by(key=key).first()
        if not config:
            return jsonify({'error': 'Configuração não encontrada'}), 404
        
        return jsonify(config.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': 'Erro interno do servidor'}), 500

@casinofound_bp.route('/config/<key>', methods=['POST'])
def set_config(key):
    try:
        # Verificar autorização (simplificado)
        auth_header = request.headers.get('Authorization')
        if not auth_header or auth_header != 'Bearer admin-token':
            return jsonify({'error': 'Não autorizado'}), 401
        
        data = request.get_json()
        value = data.get('value', '')
        
        config = SiteConfig.query.filter_by(key=key).first()
        if config:
            config.value = value
            config.updated_at = datetime.utcnow()
        else:
            config = SiteConfig(key=key, value=value)
            db.session.add(config)
        
        db.session.commit()
        
        return jsonify({'message': 'Configuração guardada com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

# Health check
@casinofound_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }), 200

