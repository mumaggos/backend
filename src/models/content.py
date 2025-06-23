from src.database import db
from datetime import datetime

class Content(db.Model):
    __tablename__ = 'contents'
    
    content_id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.String(50), nullable=False)
    section_id = db.Column(db.String(50), nullable=False)
    content_type = db.Column(db.String(20), nullable=False)  # texto, imagem, vídeo
    content_value = db.Column(db.Text, nullable=False)
    language_code = db.Column(db.String(2), nullable=False, default='pt')
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    updated_by = db.Column(db.String(42), db.ForeignKey('users.wallet_address'), nullable=True)
    
    def __init__(self, page_id, section_id, content_type, content_value, language_code='pt', updated_by=None):
        self.page_id = page_id
        self.section_id = section_id
        self.content_type = content_type
        self.content_value = content_value
        self.language_code = language_code
        self.updated_by = updated_by
        
    def to_dict(self):
        return {
            'content_id': self.content_id,
            'page_id': self.page_id,
            'section_id': self.section_id,
            'content_type': self.content_type,
            'content_value': self.content_value,
            'language_code': self.language_code,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'updated_by': self.updated_by
        }
