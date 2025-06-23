from flask import Blueprint, jsonify, request
from src.models.user import User
from src.database import db
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """Obter dados do painel administrativo"""
    
    wallet_address = request.args.get('wallet_address')
    
    if not wallet_address:
        return jsonify({'success': False, 'error': 'Endereço de carteira não fornecido'}), 400
    
    # Verificar se o utilizador é administrador
    user = User.query.filter_by(wallet_address=wallet_address).first()
    
    if not user or not user.is_admin:
        return jsonify({'success': False, 'error': 'Acesso não autorizado'}), 403
    
    # Obter estatísticas gerais
    from src.models.token import Token
    from src.models.newsletter import Newsletter
    
    total_users = User.query.count()
    total_tokens_staked = db.session.query(db.func.sum(Token.staked_amount)).scalar() or 0
    total_subscribers = Newsletter.query.filter_by(is_active=True).count()
    
    return jsonify({
        'success': True,
        'stats': {
            'total_users': total_users,
            'total_tokens_staked': total_tokens_staked,
            'total_subscribers': total_subscribers,
            'last_updated': datetime.utcnow().isoformat()
        }
    })

@admin_bp.route('/users', methods=['GET'])
def list_users():
    """Listar utilizadores (apenas para administradores)"""
    
    wallet_address = request.args.get('wallet_address')
    
    if not wallet_address:
        return jsonify({'success': False, 'error': 'Endereço de carteira não fornecido'}), 400
    
    # Verificar se o utilizador é administrador
    user = User.query.filter_by(wallet_address=wallet_address).first()
    
    if not user or not user.is_admin:
        return jsonify({'success': False, 'error': 'Acesso não autorizado'}), 403
    
    # Obter todos os utilizadores
    users = User.query.all()
    
    result = [user.to_dict() for user in users]
    
    return jsonify({
        'success': True,
        'users': result,
        'total': len(result)
    })

@admin_bp.route('/stats', methods=['GET'])
def get_stats():
    """Obter estatísticas do site (apenas para administradores)"""
    
    wallet_address = request.args.get('wallet_address')
    
    if not wallet_address:
        return jsonify({'success': False, 'error': 'Endereço de carteira não fornecido'}), 400
    
    # Verificar se o utilizador é administrador
    user = User.query.filter_by(wallet_address=wallet_address).first()
    
    if not user or not user.is_admin:
        return jsonify({'success': False, 'error': 'Acesso não autorizado'}), 403
    
    # Obter estatísticas detalhadas
    from src.models.token import Token
    from src.models.newsletter import Newsletter
    from src.models.content import Content
    
    # Estatísticas de utilizadores
    total_users = User.query.count()
    users_last_24h = User.query.filter(User.last_login > datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)).count()
    
    # Estatísticas de tokens
    total_tokens = db.session.query(db.func.sum(Token.token_amount + Token.staked_amount)).scalar() or 0
    total_staked = db.session.query(db.func.sum(Token.staked_amount)).scalar() or 0
    staking_percentage = (total_staked / total_tokens * 100) if total_tokens > 0 else 0
    
    # Estatísticas de newsletter
    total_subscribers = Newsletter.query.filter_by(is_active=True).count()
    subscribers_by_language = db.session.query(
        Newsletter.language_preference, 
        db.func.count(Newsletter.email)
    ).filter_by(is_active=True).group_by(Newsletter.language_preference).all()
    
    subscribers_lang = {lang: count for lang, count in subscribers_by_language}
    
    # Estatísticas de conteúdo
    content_by_language = db.session.query(
        Content.language_code, 
        db.func.count(Content.content_id)
    ).group_by(Content.language_code).all()
    
    content_lang = {lang: count for lang, count in content_by_language}
    
    return jsonify({
        'success': True,
        'stats': {
            'users': {
                'total': total_users,
                'active_last_24h': users_last_24h
            },
            'tokens': {
                'total': total_tokens,
                'staked': total_staked,
                'staking_percentage': round(staking_percentage, 2)
            },
            'newsletter': {
                'total_subscribers': total_subscribers,
                'by_language': subscribers_lang
            },
            'content': {
                'by_language': content_lang
            },
            'last_updated': datetime.utcnow().isoformat()
        }
    })
