from flask import Blueprint, jsonify, request
from src.models.content import Content
from src.models.user import User
from src.database import db
from datetime import datetime

content_bp = Blueprint('content', __name__)

@content_bp.route('/<page>/<language>', methods=['GET'])
def get_content(page, language):
    """Obter conteúdo de uma página específica num determinado idioma"""
    
    # Verificar se o idioma é válido
    valid_languages = ['pt', 'en', 'fr', 'cn']
    if language not in valid_languages:
        language = 'pt'  # Idioma padrão
    
    # Obter todos os conteúdos da página no idioma especificado
    contents = Content.query.filter_by(page_id=page, language_code=language).all()
    
    # Se não existir conteúdo no idioma solicitado, tentar obter em português
    if not contents and language != 'pt':
        contents = Content.query.filter_by(page_id=page, language_code='pt').all()
    
    result = {}
    for content in contents:
        result[content.section_id] = {
            'type': content.content_type,
            'value': content.content_value,
            'last_updated': content.last_updated.isoformat() if content.last_updated else None
        }
    
    return jsonify({
        'success': True,
        'page': page,
        'language': language,
        'contents': result
    })

@content_bp.route('/translations', methods=['GET'])
def get_translations():
    """Obter traduções disponíveis para todas as páginas"""
    
    # Agrupar por página e idioma
    pages = db.session.query(Content.page_id).distinct().all()
    
    result = {}
    for page in pages:
        page_id = page[0]
        languages = db.session.query(Content.language_code).filter_by(page_id=page_id).distinct().all()
        result[page_id] = [lang[0] for lang in languages]
    
    return jsonify({
        'success': True,
        'translations': result
    })

# Rotas administrativas para gestão de conteúdo
@content_bp.route('/admin/update', methods=['POST'])
def update_content():
    """Atualizar conteúdo (apenas para administradores)"""
    
    data = request.json
    
    if not data or 'wallet_address' not in data or 'page_id' not in data or 'section_id' not in data or 'content_type' not in data or 'content_value' not in data or 'language_code' not in data:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    
    wallet_address = data['wallet_address']
    
    # Verificar se o utilizador é administrador
    user = User.query.filter_by(wallet_address=wallet_address).first()
    
    if not user or not user.is_admin:
        return jsonify({'success': False, 'error': 'Acesso não autorizado'}), 403
    
    # Verificar se o conteúdo já existe
    content = Content.query.filter_by(
        page_id=data['page_id'],
        section_id=data['section_id'],
        language_code=data['language_code']
    ).first()
    
    if content:
        # Atualizar conteúdo existente
        content.content_type = data['content_type']
        content.content_value = data['content_value']
        content.last_updated = datetime.utcnow()
        content.updated_by = wallet_address
    else:
        # Criar novo conteúdo
        content = Content(
            page_id=data['page_id'],
            section_id=data['section_id'],
            content_type=data['content_type'],
            content_value=data['content_value'],
            language_code=data['language_code'],
            updated_by=wallet_address
        )
        db.session.add(content)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'content': content.to_dict()
    })
