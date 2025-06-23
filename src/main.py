import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS

# Configuração do caminho do sistema
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Inicialização da aplicação Flask
app = Flask(__name__)
CORS(app)

# Configuração da base de dados (SQLite para simplicidade)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///casinofound.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'casinofound-secret-key-2024'

# Configuração multilíngue
app.config['BABEL_DEFAULT_LOCALE'] = 'pt'
app.config['BABEL_SUPPORTED_LOCALES'] = ['pt', 'en', 'fr', 'cn']

# Inicializar base de dados
from src.database import db
db.init_app(app)

# Rota de teste/status
@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'online',
        'version': '1.0.0',
        'name': 'CasinoFound API'
    })

# Importar e registar blueprints
from src.routes.auth import auth_bp
from src.routes.token import token_bp
from src.routes.content import content_bp
from src.routes.config import config_bp
from src.routes.newsletter import newsletter_bp
from src.routes.admin import admin_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(token_bp, url_prefix='/api/tokens')
app.register_blueprint(content_bp, url_prefix='/api/content')
app.register_blueprint(config_bp, url_prefix='/api/config')
app.register_blueprint(newsletter_bp, url_prefix='/api/newsletter')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

# Inicialização dos modelos e dados iniciais
def init_database():
    from src.models import init_db
    with app.app_context():
        init_db(db)

if __name__ == '__main__':
    # Inicializar base de dados
    init_database()
    
    # Iniciar servidor
    app.run(host='0.0.0.0', port=5000, debug=True)

