# app/models/communication.py
from app import db
from datetime import datetime
from app.utils import get_utc_now
from app.utils.encryption import EncryptedType

class Communication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipient = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    _content_html = db.Column('content_html', EncryptedType, nullable=True)  # Contenu HTML chiffré (nom interne)
    _content_text = db.Column('content_text', EncryptedType, nullable=True)  # Contenu texte chiffré (nom interne)
    type = db.Column(db.String(50), nullable=False)  # Ex: 'password_reset', 'task_notification', etc.
    status = db.Column(db.String(20), nullable=False, default='sent')  # sent, failed
    sent_at = db.Column(db.DateTime, default=get_utc_now)
    
    # Référence optionnelle à un utilisateur
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', backref='communications_received', lazy=True, foreign_keys=[user_id])
    
    # Autres références optionnelles
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    
    # Référence à l'utilisateur qui a déclenché l'envoi (si applicable)
    triggered_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    triggered_by = db.relationship('User', 
                                foreign_keys=[triggered_by_id],
                                backref='communications_triggered', 
                                lazy=True)
    
    def __repr__(self):
        return f"Communication('{self.type}', to: '{self.recipient}', sent: '{self.sent_at}')"
    
    def decrypt_data(self, encrypted_value):
        """Déchiffre une valeur si elle est chiffrée"""
        if not encrypted_value or not isinstance(encrypted_value, str) or not encrypted_value.startswith('gAAA'):
            return encrypted_value
            
        try:
            from flask import current_app
            from cryptography.fernet import Fernet
            
            key = current_app.config.get('ENCRYPTION_KEY')
            if not key:
                return "[Erreur: Clé de chiffrement manquante]"
                
            f = Fernet(key)
            decrypted_data = f.decrypt(encrypted_value.encode('utf-8'))
            return decrypted_data.decode('utf-8')
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Erreur lors du déchiffrement: {str(e)}")
            return "[Erreur de déchiffrement]"
    
    # Propriétés pour accéder aux données déchiffrées automatiquement
    @property
    def content_html(self):
        return self.decrypt_data(self._content_html)
    
    @content_html.setter
    def content_html(self, value):
        self._content_html = value
    
    @property
    def content_text(self):
        return self.decrypt_data(self._content_text)
    
    @content_text.setter
    def content_text(self, value):
        self._content_text = value