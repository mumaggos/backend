from flask import Blueprint, jsonify, request
from src.models.newsletter import Newsletter
from src.database import db
from datetime import datetime

newsletter_bp = Blueprint('newsletter', __name__)

@newsletter_bp.route('/subscribe', methods=['POST'])
def subscribe():
    """Subscrever newsletter"""
    
    data = request.json
    
    if not data or 'email' not in data:
        return jsonify({'success': False, 'error': 'Email não fornecido'}), 400
    
    email = data['email']
    language_preference = data.get('language_preference', 'pt')
    
    # Verificar se o email já está subscrito
    subscription = Newsletter.query.filter_by(email=email).first()
    
    if subscription:
        if subscription.is_active:
            return jsonify({'success': False, 'error': 'Email já subscrito'}), 400
        else:
            # Reativar subscrição
            subscription.is_active = True
            subscription.language_preference = language_preference
            db.session.commit()
            return jsonify({'success': True, 'message': 'Subscrição reativada'})
    
    # Criar nova subscrição
    subscription = Newsletter(
        email=email,
        language_preference=language_preference
    )
    db.session.add(subscription)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Subscrição realizada com sucesso'
    })

@newsletter_bp.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    """Cancelar subscrição da newsletter"""
    
    data = request.json
    
    if not data or 'email' not in data:
        return jsonify({'success': False, 'error': 'Email não fornecido'}), 400
    
    email = data['email']
    
    # Verificar se o email está subscrito
    subscription = Newsletter.query.filter_by(email=email).first()
    
    if not subscription or not subscription.is_active:
        return jsonify({'success': False, 'error': 'Email não subscrito'}), 404
    
    # Desativar subscrição
    subscription.is_active = False
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Subscrição cancelada com sucesso'
    })

@newsletter_bp.route('/admin/list', methods=['GET'])
def list_subscribers():
    """Listar subscritores (apenas para administradores)"""
    
    wallet_address = request.args.get('wallet_address')
    
    if not wallet_address:
        return jsonify({'success': False, 'error': 'Endereço de carteira não fornecido'}), 400
    
    # Verificar se o utilizador é administrador
    from src.models.user import User
    user = User.query.filter_by(wallet_address=wallet_address).first()
    
    if not user or not user.is_admin:
        return jsonify({'success': False, 'error': 'Acesso não autorizado'}), 403
    
    # Obter todos os subscritores ativos
    subscribers = Newsletter.query.filter_by(is_active=True).all()
    
    result = [subscriber.to_dict() for subscriber in subscribers]
    
    return jsonify({
        'success': True,
        'subscribers': result,
        'total': len(result)
    })
