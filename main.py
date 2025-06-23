import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS

# Configuração do caminho do sistema
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Inicialização da aplicação Flask
app = Flask(__name__)
CORS(app, origins="*")

# Configuração da base de dados
# Para desenvolvimento local: SQLite
# Para produção (Render): PostgreSQL
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Produção - PostgreSQL no Render
    # Corrigir URL se necessário (algumas versões do psycopg2 requerem postgresql:// em vez de postgres://)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print(f"Usando PostgreSQL: {database_url[:50]}...")
else:
    # Desenvolvimento - SQLite local
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///casinofound.db'
    print("Usando SQLite local")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'casinofound-secret-key-2024')

# Configuração multilíngue
app.config['BABEL_DEFAULT_LOCALE'] = 'pt'
app.config['BABEL_SUPPORTED_LOCALES'] = ['pt', 'en', 'fr', 'cn']

# Inicializar base de dados
from src.database import db
db.init_app(app)

# Rota de teste/status
@app.route('/api/status', methods=['GET'])
def status():
    try:
        # Testar conexão com a base de dados
        from sqlalchemy import text
        with db.engine.connect() as connection:
            connection.execute(text('SELECT 1'))
        db_status = 'PostgreSQL' if database_url else 'SQLite'
        db_connected = True
    except Exception as e:
        db_status = f'Error: {str(e)}'
        db_connected = False
    
    return jsonify({
        'status': 'online',
        'version': '1.0.0',
        'name': 'CasinoFound API',
        'database': db_status,
        'database_connected': db_connected,
        'environment': 'production' if database_url else 'development'
    })

# Rota raiz para verificação
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'CasinoFound API está online',
        'status': 'success',
        'endpoints': [
            '/api/status',
            '/api/auth/*',
            '/api/tokens/*',
            '/api/content/*',
            '/api/config/*',
            '/api/newsletter/*',
            '/api/admin/*'
        ]
    })

# Importar e registar blueprints
try:
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
    print("Blueprints registados com sucesso")
except Exception as e:
    print(f"Erro ao registar blueprints: {e}")

# Inicialização da base de dados
def init_database():
    """Inicializa a base de dados e dados iniciais"""
    try:
        with app.app_context():
            # Criar todas as tabelas
            db.create_all()
            print("Tabelas criadas com sucesso")
            
            # Importar e executar inicialização de dados
            from src.models import init_db
            init_db(db)
            
            print("Base de dados inicializada com sucesso!")
            
    except Exception as e:
        print(f"Erro ao inicializar base de dados: {e}")
        # Não falhar o deploy por causa de erros de inicialização
        pass

# Inicializar base de dados na primeira execução
if __name__ == '__main__':
    init_database()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
else:
    # Para deployment (Render/Vercel)
    init_database()

# Exportar app para servidores WSGI
application = app

