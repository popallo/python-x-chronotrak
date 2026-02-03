from app import db
from datetime import datetime, timezone
from app.utils.encryption import EncryptedType
from cryptography.fernet import Fernet
from flask import current_app
from app.utils.slug_utils import update_slug

# Cache pour l'instance Fernet
_fernet_instance = None

def get_fernet():
    global _fernet_instance
    if _fernet_instance is None:
        key = current_app.config.get('ENCRYPTION_KEY')
        if not key:
            current_app.logger.error("Clé de chiffrement manquante dans la configuration")
            return None
        _fernet_instance = Fernet(key)
    return _fernet_instance

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    contact_name = db.Column(db.String(100), nullable=True, index=True)
    _email = db.Column('email', EncryptedType, nullable=True)  # Chiffré (nom interne)
    _phone = db.Column('phone', EncryptedType, nullable=True)  # Chiffré (nom interne)
    _address = db.Column('address', EncryptedType, nullable=True)  # Chiffré (nom interne)
    _notes = db.Column('notes', EncryptedType, nullable=True)  # Chiffré (nom interne)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    # Relations
    projects = db.relationship('Project', backref='client', lazy='joined', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.Index('idx_client_name_slug', 'name', 'slug'),
        db.Index('idx_client_created_at', 'created_at'),
    )
    
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
            f = get_fernet()
            if f is None:
                return "[Erreur: Clé de chiffrement manquante]"
                
            decrypted_data = f.decrypt(encrypted_value.encode('utf-8'))
            return decrypted_data.decode('utf-8')
        except Exception as e:
            current_app.logger.error(f"Erreur lors du déchiffrement: {str(e)}")
            current_app.logger.error(f"Valeur chiffrée: {encrypted_value[:20]}...")
            return "[Erreur de déchiffrement]"
    
    # Propriétés pour accéder aux données déchiffrées automatiquement
    @property
    def email(self):
        return self.decrypt_data(self._email)
    
    @email.setter
    def email(self, value):
        self._email = value
    
    @property
    def phone(self):
        return self.decrypt_data(self._phone)
    
    @phone.setter
    def phone(self, value):
        self._phone = value
    
    @property
    def address(self):
        return self.decrypt_data(self._address)
    
    @address.setter
    def address(self, value):
        self._address = value
    
    @property
    def notes(self):
        return self.decrypt_data(self._notes)
    
    @notes.setter
    def notes(self, value):
        self._notes = value
    
    # Propriétés de compatibilité (anciennes méthodes)
    @property
    def safe_email(self):
        return self.email
    
    @property
    def safe_phone(self):
        return self.phone
    
    @property
    def safe_address(self):
        return self.address
    
    @property
    def safe_notes(self):
        return self.notes