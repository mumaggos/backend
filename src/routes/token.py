from flask import Blueprint, jsonify, request
from src.models.token import Token
from src.models.user import User
from src.database import db
from datetime import datetime
import json

token_bp = Blueprint('token', __name__)

@token_bp.route('/balance', methods=['GET'])
def get_balance():
    wallet_address = request.args.get('wallet_address')
    
    if not wallet_address:
        return jsonify({'success': False, 'error': 'Endereço de carteira não fornecido'}), 400
    
    # Verificar se o utilizador existe
    user = User.query.filter_by(wallet_address=wallet_address).first()
    
    if not user:
        return jsonify({'success': False, 'error': 'Utilizador não encontrado'}), 404
    
    # Obter informações de tokens
    token_info = Token.query.filter_by(wallet_address=wallet_address).first()
    
    if not token_info:
        # Criar registo de tokens vazio
        token_info = Token(wallet_address=wallet_address)
        db.session.add(token_info)
        db.session.commit()
    
    return jsonify({
        'success': True,
        'token_info': token_info.to_dict()
    })

@token_bp.route('/staked', methods=['GET'])
def get_staked():
    wallet_address = request.args.get('wallet_address')
    
    if not wallet_address:
        return jsonify({'success': False, 'error': 'Endereço de carteira não fornecido'}), 400
    
    # Obter informações de tokens
    token_info = Token.query.filter_by(wallet_address=wallet_address).first()
    
    if not token_info:
        return jsonify({
            'success': True,
            'staked_amount': 0,
            'staking_start_date': None,
            'last_reward_date': None
        })
    
    return jsonify({
        'success': True,
        'staked_amount': token_info.staked_amount,
        'staking_start_date': token_info.staking_start_date.isoformat() if token_info.staking_start_date else None,
        'last_reward_date': token_info.last_reward_date.isoformat() if token_info.last_reward_date else None
    })

@token_bp.route('/stake', methods=['POST'])
def stake_tokens():
    data = request.json
    
    if not data or 'wallet_address' not in data or 'amount' not in data:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    
    wallet_address = data['wallet_address']
    amount = float(data['amount'])
    
    if amount <= 0:
        return jsonify({'success': False, 'error': 'Quantidade inválida'}), 400
    
    # Obter informações de tokens
    token_info = Token.query.filter_by(wallet_address=wallet_address).first()
    
    if not token_info:
        return jsonify({'success': False, 'error': 'Utilizador não possui tokens'}), 404
    
    if token_info.token_amount < amount:
        return jsonify({'success': False, 'error': 'Saldo insuficiente'}), 400
    
    # Atualizar saldos
    token_info.token_amount -= amount
    token_info.staked_amount += amount
    
    if not token_info.staking_start_date:
        token_info.staking_start_date = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'token_info': token_info.to_dict()
    })

@token_bp.route('/unstake', methods=['POST'])
def unstake_tokens():
    data = request.json
    
    if not data or 'wallet_address' not in data or 'amount' not in data:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    
    wallet_address = data['wallet_address']
    amount = float(data['amount'])
    
    if amount <= 0:
        return jsonify({'success': False, 'error': 'Quantidade inválida'}), 400
    
    # Obter informações de tokens
    token_info = Token.query.filter_by(wallet_address=wallet_address).first()
    
    if not token_info:
        return jsonify({'success': False, 'error': 'Utilizador não possui tokens em stake'}), 404
    
    if token_info.staked_amount < amount:
        return jsonify({'success': False, 'error': 'Saldo em stake insuficiente'}), 400
    
    # Verificar período mínimo de 30 dias
    if token_info.staking_start_date:
        days_staked = (datetime.utcnow() - token_info.staking_start_date).days
        if days_staked < 30:
            return jsonify({'success': False, 'error': 'Período mínimo de stake é de 30 dias'}), 400
    
    # Atualizar saldos
    token_info.staked_amount -= amount
    token_info.token_amount += amount
    
    if token_info.staked_amount == 0:
        token_info.staking_start_date = None
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'token_info': token_info.to_dict()
    })

@token_bp.route('/percentage', methods=['GET'])
def get_percentage():
    wallet_address = request.args.get('wallet_address')
    
    if not wallet_address:
        return jsonify({'success': False, 'error': 'Endereço de carteira não fornecido'}), 400
    
    # Obter informações de tokens
    token_info = Token.query.filter_by(wallet_address=wallet_address).first()
    
    if not token_info:
        return jsonify({
            'success': True,
            'percentage': 0,
            'total_tokens': 0,
            'total_supply': 21000000
        })
    
    total_tokens = token_info.token_amount + token_info.staked_amount
    total_supply = 21000000  # Total supply conforme whitepaper
    
    percentage = (total_tokens / total_supply) * 100 if total_supply > 0 else 0
    
    return jsonify({
        'success': True,
        'percentage': round(percentage, 6),
        'total_tokens': total_tokens,
        'total_supply': total_supply
    })
