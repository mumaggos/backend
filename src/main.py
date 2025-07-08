import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import json
import logging
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do Flask
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your_super_secret_key_here")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///casinofound.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configurar CORS para permitir requisições do frontend
CORS(app, origins="*")

# Inicializar banco de dados
db = SQLAlchemy(app)

# Configuração Web3 com as suas credenciais (carregadas de variáveis de ambiente)
INFURA_API_KEY = os.getenv("INFURA_API_KEY")
POLYGON_RPC_URL = os.getenv("POLYGON_RPC_URL", f"https://polygon-mainnet.infura.io/v3/{INFURA_API_KEY}")
WALLETCONNECT_PROJECT_ID = os.getenv("WALLETCONNECT_PROJECT_ID")
EMAILJS_SERVICE_ID = os.getenv("EMAILJS_SERVICE_ID")
ADMIN_PRIVATE_KEY = os.getenv("ADMIN_PRIVATE_KEY") # Chave privada para assinar transações

# Endereços dos contratos (carregados de variáveis de ambiente)
CFD_TOKEN_ADDRESS = os.getenv("CFD_TOKEN_ADDRESS")
ICO_PHASE1_ADDRESS = os.getenv("ICO_PHASE1_ADDRESS")
AFFILIATE_MANAGER_ADDRESS = os.getenv("AFFILIATE_MANAGER_ADDRESS")

# Inicializar Web3
w3 = Web3(Web3.HTTPProvider(POLYGON_RPC_URL))

# Carregar ABIs dos arquivos JSON
def load_abi(filename):
    filepath = os.path.join(os.path.dirname(__file__), "abi", filename)
    with open(filepath, "r") as f:
        return json.load(f)

CFD_TOKEN_ABI = load_abi("CFD.json")
AFFILIATE_MANAGER_ABI = load_abi("AffiliateManager.json")
ICO_PHASE1_ABI = load_abi("ICOPhase1.json")

# Inicializar contratos
cfd_token_contract = w3.eth.contract(address=CFD_TOKEN_ADDRESS, abi=CFD_TOKEN_ABI)
affiliate_manager_contract = w3.eth.contract(address=AFFILIATE_MANAGER_ADDRESS, abi=AFFILIATE_MANAGER_ABI)
ico_phase1_contract = w3.eth.contract(address=ICO_PHASE1_ADDRESS, abi=ICO_PHASE1_ABI)

# Modelos de banco de dados
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wallet_address = db.Column(db.String(42), unique=True, nullable=False)
    cfd_balance = db.Column(db.Float, default=0.0)
    staked_tokens = db.Column(db.Float, default=0.0)
    earned_rewards = db.Column(db.Float, default=0.0)
    affiliate_earnings = db.Column(db.Float, default=0.0)
    referral_code = db.Column(db.String(42), unique=True)
    referred_by = db.Column(db.String(42))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Newsletter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wallet_address = db.Column(db.String(42), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # buy, stake, unstake, affiliate
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    tx_hash = db.Column(db.String(66))
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Criar tabelas
with app.app_context():
    db.create_all()

# Rotas da API

@app.route(\"/health\", methods=[\"GET\"])
def health_check():
    try:
        w3_connected = w3.is_connected()
    except Exception:
        w3_connected = False

    db_connected = False
    try:
        db.session.execute(db.text(\"SELECT 1\"))
        db_connected = True
    except Exception:
        pass

    return jsonify({
        \"status\": \"healthy\",
        \"timestamp\": datetime.utcnow().isoformat(),
        \"web3_connected\": w3_connected,
        \"database_connected\": db_connected
    })

@app.route(\"/api/user_data\", methods=[\"GET\"])
def get_user_data():
    \"\"\"Obter dados do usuário\"\"\"
    wallet_address = request.args.get(\'wallet_address\')
    
    if not wallet_address:
        return jsonify({\'error\': \'Endereço da carteira é obrigatório\'}), 400
    
    try:
        # Buscar ou criar usuário
        user = User.query.filter_by(wallet_address=wallet_address).first()
        if not user:
            user = User(
                wallet_address=wallet_address,
                referral_code=wallet_address,
                cfd_balance=0.0,
                staked_tokens=0.0,
                earned_rewards=0.0,
                affiliate_earnings=0.0
            )
            db.session.add(user)
            db.session.commit()
        
        # Buscar saldo real do contrato (se possível)
        try:
            real_balance = cfd_token_contract.functions.balanceOf(wallet_address).call()
            user.cfd_balance = real_balance / (10**18)  # Converter de wei para tokens
        except Exception as e:
            app.logger.warning(f\"Erro ao buscar saldo real: {e}\")
        
        # Calcular percentagem do total supply
        total_supply = 21000000  # 21 milhões de tokens
        cfd_percentage = (user.cfd_balance / total_supply) * 100 if total_supply > 0 else 0
        
        return jsonify({
            \"cfd_balance\": f\"{user.cfd_balance:.2f}\",
            \"total_supply\": f\"{total_supply:,}\",
            \"cfd_percentage\": f\"{cfd_percentage:.4f}\",
            \"staked_tokens\": f\"{user.staked_tokens:.2f}\",
            \"earned_rewards\": f\"{user.earned_rewards:.4f}\",
            \"affiliate_earnings\": f\"{user.affiliate_earnings:.4f}\"
        })
        
    except Exception as e:
        app.logger.error(f\"Erro ao obter dados do usuário: {e}\")
        return jsonify({\'error\': \'Erro interno do servidor\'}), 500

@app.route(\"/api/buy_tokens\", methods=[\"POST\"])
def buy_tokens():
    \"\"\"Comprar tokens CFD\"\"\"
    data = request.get_json()
    wallet_address = data.get(\'wallet_address\')
    amount = float(data.get(\'amount\', 0))
    currency = data.get(\'currency\', \'usdt\')
    
    if not wallet_address or amount <= 0:
        return jsonify({\'error\': \'Dados inválidos\'}), 400
    
    try:
        # Buscar ou criar usuário
        user = User.query.filter_by(wallet_address=wallet_address).first()
        if not user:
            user = User(wallet_address=wallet_address, referral_code=wallet_address)
            db.session.add(user)
        
        # Simular compra (em produção, interagir com contrato real)
        price_per_token = 0.02  # Preço da Fase 1
        tokens_to_receive = amount / price_per_token
        
        # Em um ambiente real, você faria a interação com o contrato aqui
        # Exemplo (requer ADMIN_PRIVATE_KEY e gas):
        # if ADMIN_PRIVATE_KEY:
        #     admin_account = Account.from_key(ADMIN_PRIVATE_KEY)
        #     nonce = w3.eth.get_transaction_count(admin_account.address)
        #     tx = cfd_token_contract.functions.transfer(wallet_address, int(tokens_to_receive * (10**18))).build_transaction({
        #         \'chainId\': w3.eth.chain_id,
        #         \'gas\': 2000000, # Ajuste o gas conforme necessário
        #         \'gasPrice\': w3.eth.gas_price,
        #         \'nonce\': nonce,
        #     })
        #     signed_tx = w3.eth.account.sign_transaction(tx, private_key=ADMIN_PRIVATE_KEY)
        #     tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        #     w3.eth.wait_for_transaction_receipt(tx_hash)
        #     tx_hash_str = tx_hash.hex()
        # else:
        #     tx_hash_str = \"simulated_tx_hash\"
        
        tx_hash_str = \"simulated_tx_hash\"

        # Registrar transação
        new_transaction = Transaction(
            wallet_address=wallet_address,
            transaction_type=\'buy\',
            amount=tokens_to_receive,
            currency=\'CFD\',
            tx_hash=tx_hash_str,
            status=\'confirmed\'
        )
        db.session.add(new_transaction)
        
        user.cfd_balance += tokens_to_receive
        db.session.commit()
        
        return jsonify({
            \"message\": \"Compra simulada com sucesso!\",
            \"tokens_received\": tokens_to_receive,
            \"tx_hash\": tx_hash_str
        })
        
    except Exception as e:
        app.logger.error(f\"Erro ao comprar tokens: {e}\")
        return jsonify({\'error\': \'Erro interno do servidor\'}), 500

@app.route(\"/api/stake_tokens\", methods=[\"POST\"])
def stake_tokens():
    \"\"\"Fazer staking de tokens CFD\"\"\"
    data = request.get_json()
    wallet_address = data.get(\'wallet_address\')
    amount = float(data.get(\'amount\', 0))
    
    if not wallet_address or amount <= 0:
        return jsonify({\'error\': \'Dados inválidos\'}), 400
    
    try:
        user = User.query.filter_by(wallet_address=wallet_address).first()
        if not user or user.cfd_balance < amount:
            return jsonify({\'error\': \'Saldo insuficiente de CFD\'}), 400
        
        # Simular staking
        tx_hash_str = \"simulated_stake_tx_hash\"

        new_transaction = Transaction(
            wallet_address=wallet_address,
            transaction_type=\'stake\',
            amount=amount,
            currency=\'CFD\',
            tx_hash=tx_hash_str,
            status=\'confirmed\'
        )
        db.session.add(new_transaction)
        
        user.cfd_balance -= amount
        user.staked_tokens += amount
        db.session.commit()
        
        return jsonify({
            \"message\": \"Staking simulado com sucesso!\",
            \"staked_amount\": amount,
            \"tx_hash\": tx_hash_str
        })
        
    except Exception as e:
        app.logger.error(f\"Erro ao fazer staking: {e}\")
        return jsonify({\'error\': \'Erro interno do servidor\'}), 500

@app.route(\"/api/unstake_tokens\", methods=[\"POST\"])
def unstake_tokens():
    \"\"\"Remover staking de tokens CFD\"\"\"
    data = request.get_json()
    wallet_address = data.get(\'wallet_address\')
    amount = float(data.get(\'amount\', 0))
    
    if not wallet_address or amount <= 0:
        return jsonify({\'error\': \'Dados inválidos\'}), 400
    
    try:
        user = User.query.filter_by(wallet_address=wallet_address).first()
        if not user or user.staked_tokens < amount:
            return jsonify({\'error\': \'Tokens em staking insuficientes\'}), 400
        
        # Simular unstaking
        tx_hash_str = \"simulated_unstake_tx_hash\"

        new_transaction = Transaction(
            wallet_address=wallet_address,
            transaction_type=\'unstake\',
            amount=amount,
            currency=\'CFD\',
            tx_hash=tx_hash_str,
            status=\'confirmed\'
        )
        db.session.add(new_transaction)
        
        user.cfd_balance += amount
        user.staked_tokens -= amount
        db.session.commit()
        
        return jsonify({
            \"message\": \"Unstaking simulado com sucesso!\",
            \"unstaked_amount\": amount,
            \"tx_hash\": tx_hash_str
        })
        
    except Exception as e:
        app.logger.error(f\"Erro ao remover staking: {e}\")
        return jsonify({\'error\': \'Erro interno do servidor\'}), 500

@app.route(\"/api/subscribe_newsletter\", methods=[\"POST\"])
def subscribe_newsletter():
    \"\"\"Subscrever newsletter\"\"\"
    data = request.get_json()
    email = data.get(\'email\')
    
    if not email:
        return jsonify({\'error\': \'Email é obrigatório\'}), 400
    
    try:
        newsletter_entry = Newsletter.query.filter_by(email=email).first()
        if newsletter_entry:
            if newsletter_entry.is_active:
                return jsonify({\'message\': \'Email já subscrito\'})
            else:
                newsletter_entry.is_active = True
                newsletter_entry.subscribed_at = datetime.utcnow()
                db.session.commit()
                return jsonify({\'message\': \'Subscrição reativada com sucesso!\'})
        else:
            new_entry = Newsletter(email=email)
            db.session.add(new_entry)
            db.session.commit()
            
            # Enviar email de confirmação (usando EmailJS ou SMTP)
            # email_user = os.getenv("EMAIL_USER")
            # email_password = os.getenv("EMAIL_PASSWORD")
            # if email_user and email_password:
            #     try:
            #         msg = MIMEMultipart(\'alternative\')
            #         msg[\'Subject\'] = \'Confirmação de Subscrição - CasinoFound\'
            #         msg[\'From\'] = email_user
            #         msg[\'To\'] = email
            #         
            #         text = \"Obrigado por subscrever a nossa newsletter!\"
            #         html = \"\"\"\"\"<p>Obrigado por subscrever a nossa newsletter!</p>\"\"\"\"\"
            #         
            #         part1 = MIMEText(text, \'plain\')
            #         part2 = MIMEText(html, \'html\')
            #         
            #         msg.attach(part1)
            #         msg.attach(part2)
            #         
            #         with smtplib.SMTP_SSL(\'smtp.gmail.com\', 465) as smtp:
            #             smtp.login(email_user, email_password)
            #             smtp.send_message(msg)
            #     except Exception as e:
            #         app.logger.error(f\"Erro ao enviar email de confirmação: {e}\")
            
            return jsonify({\'message\': \'Subscrito com sucesso!\'})
            
    except Exception as e:
        app.logger.error(f\"Erro ao subscrever newsletter: {e}\")
        return jsonify({\'error\': \'Erro interno do servidor\'}), 500

@app.route(\"/api/affiliate_share\", methods=[\"POST\"])
def affiliate_share():
    \"\"\"Registrar e processar partilha de afiliados\"\"\"
    data = request.get_json()
    referrer_address = data.get(\'referrer_address\')
    new_user_address = data.get(\'new_user_address\')
    
    if not referrer_address or not new_user_address:
        return jsonify({\'error\': \'Endereços de referência e novo usuário são obrigatórios\'}), 400
    
    try:
        referrer = User.query.filter_by(wallet_address=referrer_address).first()
        if not referrer:
            return jsonify({\'error\': \'Referenciador não encontrado\'}), 404
            
        new_user = User.query.filter_by(wallet_address=new_user_address).first()
        if new_user and new_user.referred_by:
            return jsonify({\'message\': \'Novo usuário já foi referido\'})
            
        if not new_user:
            new_user = User(wallet_address=new_user_address, referral_code=new_user_address)
            db.session.add(new_user)
            
        new_user.referred_by = referrer_address
        db.session.commit()
        
        # Simular pagamento de comissão (em produção, interagir com contrato real)
        # Exemplo:
        # if ADMIN_PRIVATE_KEY:
        #     admin_account = Account.from_key(ADMIN_PRIVATE_KEY)
        #     nonce = w3.eth.get_transaction_count(admin_account.address)
        #     commission_amount = w3.to_wei(0.001, \'ether\') # Exemplo de comissão
        #     tx = affiliate_manager_contract.functions.payAffiliate(referrer_address, commission_amount).build_transaction({
        #         \'chainId\': w3.eth.chain_id,
        #         \'gas\': 2000000,
        #         \'gasPrice\': w3.eth.gas_price,
        #         \'nonce\': nonce,
        #     })
        #     signed_tx = w3.eth.account.sign_transaction(tx, private_key=ADMIN_PRIVATE_KEY)
        #     tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        #     w3.eth.wait_for_transaction_receipt(tx_hash)
        #     tx_hash_str = tx_hash.hex()
        # else:
        #     tx_hash_str = \"simulated_affiliate_tx_hash\"
        
        tx_hash_str = \"simulated_affiliate_tx_hash\"

        new_transaction = Transaction(
            wallet_address=referrer_address,
            transaction_type=\'affiliate\',
            amount=0.001, # Simulado
            currency=\'MATIC\',
            tx_hash=tx_hash_str,
            status=\'confirmed\'
        )
        db.session.add(new_transaction)
        
        referrer.affiliate_earnings += 0.001 # Simulado
        db.session.commit()
        
        return jsonify({
            \"message\": \"Afiliado registrado e comissão simulada!\",
            \"referrer\": referrer_address,
            \"new_user\": new_user_address,
            \"tx_hash\": tx_hash_str
        })
        
    except Exception as e:
        app.logger.error(f\"Erro ao registrar afiliado: {e}\")
        return jsonify({\'error\': \'Erro interno do servidor\'}), 500

if __name__ == \'__main__\':
    port = int(os.environ.get(\"PORT\", 5000)) # Pega a porta da variável de ambiente ou usa 5000 como padrão
    app.run(host=\'0.0.0.0\', port=port, debug=False) # debug=False para produção


