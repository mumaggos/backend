from flask import Blueprint, jsonify, request
from src.models.config import Config
from src.models.user import User
from src.database import db
from datetime import datetime

config_bp = Blueprint('config', __name__)

@config_bp.route('/get', methods=['GET'])
def get_config():
    """Obter configurações públicas do sistema"""
    
    # Obter todas as configurações públicas
    configs = Config.query.all()
    
    result = {}
    for config in configs:
        # Não expor configurações sensíveis (como chaves privadas)
        if not config.config_key.startswith('private_'):
            result[config.config_key] = config.config_value
    
    return jsonify({
        'success': True,
        'configs': result
    })

@config_bp.route('/admin/update', methods=['POST'])
def update_config():
    """Atualizar configurações (apenas para administradores)"""
    
    data = request.json
    
    if not data or 'wallet_address' not in data or 'config_key' not in data or 'config_value' not in data:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    
    wallet_address = data['wallet_address']
    
    # Verificar se o utilizador é administrador
    user = User.query.filter_by(wallet_address=wallet_address).first()
    
    if not user or not user.is_admin:
        return jsonify({'success': False, 'error': 'Acesso não autorizado'}), 403
    
    # Verificar se a configuração já existe
    config = Config.query.filter_by(config_key=data['config_key']).first()
    
    if config:
        # Atualizar configuração existente
        config.config_value = data['config_value']
        config.last_updated = datetime.utcnow()
        config.updated_by = wallet_address
    else:
        # Criar nova configuração
        config = Config(
            config_key=data['config_key'],
            config_value=data['config_value'],
            updated_by=wallet_address
        )
        db.session.add(config)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'config': config.to_dict()
    })
