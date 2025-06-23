# Função para inicializar os modelos na base de dados
def init_db(db):
    from src.models.user import User
    from src.models.config import Config
    
    db.create_all()
    
    # Verificar se já existe um administrador
    admin_wallet = "0x435FE1f9Fe971BA37c51b25272e9e3d12a39490d"
    admin = User.query.filter_by(wallet_address=admin_wallet).first()
    
    if not admin:
        # Criar administrador
        admin = User(
            wallet_address=admin_wallet,
            username="Admin",
            preferred_language="pt",
            is_admin=True
        )
        db.session.add(admin)
        
        # Adicionar configurações iniciais
        configs = [
            Config("contract_address", "0x0000000000000000000000000000000000000000"),
            Config("total_supply", "21000000"),
            Config("ico_phase", "1"),
            Config("ico_phase1_price", "0.02"),
            Config("ico_phase2_price", "0.10"),
            Config("launch_date", "2026-01-01T00:00:00Z"),
            Config("default_language", "pt")
        ]
        
        for config in configs:
            db.session.add(config)
        
        db.session.commit()

