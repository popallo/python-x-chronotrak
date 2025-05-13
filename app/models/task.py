from app import db
from datetime import datetime
from app.utils.encryption import EncryptedType
from flask import current_app
from cryptography.fernet import Fernet
from app.utils.slug_utils import update_slug

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='à faire')  # à faire, en cours, terminé
    priority = db.Column(db.String(20), nullable=False, default='normale')  # basse, normale, haute, urgente
    estimated_time = db.Column(db.Float, nullable=True)  # en heures
    actual_time = db.Column(db.Float, nullable=True)  # en heures
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Clés étrangères
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relations
    time_entries = db.relationship('TimeEntry', backref='task', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='task', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"Task('{self.title}', Status: '{self.status}', Project: '{self.project.name}')"
    
    def __init__(self, **kwargs):
        super(Task, self).__init__(**kwargs)
        if self.title and not self.slug:
            update_slug(self)
    
    def save(self):
        """Sauvegarde l'instance et met à jour le slug si nécessaire"""
        if self.title and (not self.slug or self.title != self.slug):
            update_slug(self)
        db.session.add(self)
        db.session.commit()
        
    def clone(self):
        """Crée une copie de la tâche sans les commentaires et le temps passé"""
        return Task(
            title=f"Copie de {self.title}",
            description=self.description,
            status='à faire',  # Nouvelle tâche commence toujours à "à faire"
            priority=self.priority,
            estimated_time=self.estimated_time,
            project_id=self.project_id,
            user_id=self.user_id
        )
        
    def log_time(self, hours, user_id, description=None):
        """Enregistre du temps passé sur la tâche et le déduit du crédit du projet"""
        entry = TimeEntry(
            task_id=self.id,
            user_id=user_id,
            hours=hours,
            description=description
        )
        db.session.add(entry)
        
        # Met à jour le temps total passé sur la tâche
        if self.actual_time is None:
            self.actual_time = hours
        else:
            self.actual_time += hours
        
        # Déduit du crédit du projet
        self.project.deduct_credit(hours, self.id)


class TimeEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hours = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relation
    user = db.relationship('User', backref='time_entries', lazy=True)
    
    def __repr__(self):
        return f"TimeEntry(Task: {self.task_id}, User: {self.user.name}, Hours: {self.hours})"
    
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(EncryptedType, nullable=False)  # Contenu chiffré
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Clés étrangères
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relations
    user = db.relationship('User', backref='comments', lazy=True)
    
    def __repr__(self):
        return f"Comment(Task: {self.task_id}, User: {self.user.name}, Date: {self.created_at})"
        
    # Méthode de secours pour déchiffrer manuellement si nécessaire
    def decrypt_content(self):
        if not self.content or not isinstance(self.content, str) or not self.content.startswith('gAAA'):
            return self.content
            
        try:
            key = current_app.config.get('ENCRYPTION_KEY')
            f = Fernet(key)
            return f.decrypt(self.content.encode('utf-8')).decode('utf-8')
        except Exception as e:
            current_app.logger.error(f"Erreur lors du déchiffrement d'un commentaire: {e}")
            return "[Erreur de déchiffrement]"
    
    # Propriété pour accéder au contenu déchiffré
    @property
    def safe_content(self):
        return self.decrypt_content()