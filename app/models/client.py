from app import db
from datetime import datetime
from app.utils.encryption import EncryptedType
from cryptography.fernet import Fernet
from flask import current_app
from app.utils.slug_utils import update_slug

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    contact_name = db.Column(db.String(100), nullable=True)
    email = db.Column(EncryptedType, nullable=True)  # Chiffré
    phone = db.Column(EncryptedType, nullable=True)  # Chiffré
    address = db.Column(EncryptedType, nullable=True)  # Chiffré
    notes = db.Column(EncryptedType, nullable=True)  # Chiffré
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    projects = db.relationship('Project', backref='client', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"Client('{self.name}', '{self.email}')"
    
    def __init__(self, **kwargs):
        super(Client, self).__init__(**kwargs)
        if self.name and not self.slug:
            update_slug(self)
    
    def save(self):
        """Sauvegarde l'instance et met à jour le slug si nécessaire"""
        if self.name and (not self.slug or self.name != self.slug):
            update_slug(self)
        db.session.add(self)
        db.session.commit()
    
    # Méthode de secours pour déchiffrer manuellement si nécessaire
    def decrypt_data(self, encrypted_value):
        if not encrypted_value or not encrypted_value.startswith('gAAA'):
            return encrypted_value
            
        try:
            key = current_app.config.get('ENCRYPTION_KEY')
            f = Fernet(key)
            return f.decrypt(encrypted_value.encode('utf-8')).decode('utf-8')
        except Exception as e:
            current_app.logger.error(f"Erreur lors du déchiffrement: {e}")
            return "[Erreur de déchiffrement]"
    
    # Propriétés pour accéder aux données déchiffrées
    @property
    def safe_email(self):
        return self.decrypt_data(self.email)
    
    @property
    def safe_phone(self):
        return self.decrypt_data(self.phone)
    
    @property
    def safe_address(self):
        return self.decrypt_data(self.address)
    
    @property
    def safe_notes(self):
        return self.decrypt_data(self.notes)