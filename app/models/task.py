from app import db
from datetime import datetime
from app.utils.encryption import EncryptedType
from flask import current_app
from cryptography.fernet import Fernet
from app.utils.slug_utils import update_slug

class ChecklistItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(255), nullable=False)
    is_checked = db.Column(db.Boolean, default=False)
    position = db.Column(db.Integer, default=0)  # Pour maintenir l'ordre des éléments
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Clé étrangère
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    
    def __repr__(self):
        return f"ChecklistItem('{self.content}', Checked: {self.is_checked}, Task: {self.task_id})"

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
    checklist_items = db.relationship('ChecklistItem', backref='task', lazy=True, cascade='all, delete-orphan', order_by='ChecklistItem.position')
    
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
        
    def add_checklist_item(self, content, position=None):
        """Ajoute un élément à la checklist"""
        if position is None:
            # Si aucune position n'est spécifiée, ajouter à la fin
            position = len(self.checklist_items)
            
        item = ChecklistItem(
            content=content,
            position=position,
            task_id=self.id
        )
        db.session.add(item)
        db.session.commit()
        return item
        
    def parse_checklist_shortcode(self, shortcode):
        """Parse un shortcode de type tasks["item1", "item2"] et ajoute les éléments à la checklist"""
        import re
        
        # Expression régulière pour extraire les éléments entre crochets
        pattern = r'tasks\[(.*?)\]'
        match = re.search(pattern, shortcode)
        
        if match:
            # Extraire le contenu entre crochets
            content = match.group(1)
            
            # Diviser par les virgules et nettoyer les guillemets
            items = [item.strip().strip('"\'') for item in content.split(',')]
            
            # Ajouter chaque élément à la checklist
            for item in items:
                if item:  # Ignorer les éléments vides
                    self.add_checklist_item(item)
                    
            return True
        return False

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
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    
    # Relations
    user = db.relationship('User', backref='comments', lazy=True)
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True)
    
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