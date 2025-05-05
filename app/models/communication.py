# app/models/communication.py
from app import db
from datetime import datetime
from app.utils import get_utc_now
from app.utils.encryption import EncryptedType

class Communication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipient = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content_html = db.Column(EncryptedType, nullable=True)  # Contenu HTML chiffré
    content_text = db.Column(EncryptedType, nullable=True)  # Contenu texte chiffré
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