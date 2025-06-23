from flask import Blueprint, jsonify, request
from src.models.user import User
from src.database import db
from datetime import datetime
import json

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/connect', methods=['POST'])
def connect():
    data = request.json
    
    if not data or 'wallet_address' not in data or 'signature' not in data or 'message' not in data:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    
    wallet_address = data['wallet_address']
    signature = data['signature']
    message = data['message']
    
    # Verificar assinatura
    try:
        w3 = Web3()
        message_hash = encode_defunct(text=message)
        recovered_address = w3.eth.account.recover_message(message_hash, signature=signature)
        
        if recovered_address.lower() != wallet_address.lower():
            return jsonify({'success': False, 'error': 'Assinatura inválida'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro na verificação da assinatura: {str(e)}'}), 500
    
    # Verificar se o utilizador existe
    user = User.query.filter_by(wallet_address=wallet_address).first()
    
    if not user:
        # Criar novo utilizador
        user = User(wallet_address=wallet_address)
        db.session.add(user)
    
    # Atualizar último login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'user': user.to_dict(),
        'is_admin': user.is_admin
    })

@auth_bp.route('/verify', methods=['GET'])
def verify():
    wallet_address = request.args.get('wallet_address')
    
    if not wallet_address:
        return jsonify({'success': False, 'error': 'Endereço de carteira não fornecido'}), 400
    
    user = User.query.filter_by(wallet_address=wallet_address).first()
    
    if not user:
        return jsonify({'success': False, 'error': 'Utilizador não encontrado'}), 404
    
    return jsonify({
        'success': True,
        'user': user.to_dict(),
        'is_admin': user.is_admin
    })

@auth_bp.route('/disconnect', methods=['POST'])
def disconnect():
    return jsonify({'success': True})
