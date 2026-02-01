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
    estimated_minutes = db.Column(db.Integer, nullable=True)  # en minutes
    actual_minutes = db.Column(db.Integer, nullable=True)  # en minutes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    is_pinned = db.Column(db.Boolean, nullable=False, default=False)  # Pour épingler les tâches importantes
    is_archived = db.Column(db.Boolean, nullable=False, default=False)  # Pour archiver les tâches terminées
    archived_at = db.Column(db.DateTime, nullable=True)  # Date d'archivage
    position = db.Column(db.Integer, default=0)  # Pour maintenir l'ordre des tâches dans les colonnes
    
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
        # Toujours mettre à jour le slug si le titre existe
        if self.title:
            update_slug(self)
        db.session.add(self)
        db.session.commit()
        
    def clone(self, clone_checklist_items: bool = True):
        """
        Crée une copie de la tâche sans les commentaires et le temps passé.
        
        Par défaut, la checklist (sous-tâches) est aussi clonée, mais:
        - l'état d'avancement des éléments est réinitialisé (is_checked = False)
        - aucun historique de temps n'est cloné (TimeEntry n'est pas dupliqué)
        """
        cloned_task = Task(
            title=f"Copie de {self.title}",
            description=self.description,
            status='à faire',  # Nouvelle tâche commence toujours à "à faire"
            priority=self.priority,
            estimated_minutes=self.estimated_minutes,
            project_id=self.project_id,
            user_id=self.user_id
        )
        # Le slug sera automatiquement généré dans __init__
        
        if clone_checklist_items:
            # Cloner le contenu et l'ordre de la checklist, sans cloner l'état "fait"
            # (on repart sur une nouvelle checklist à cocher).
            for item in self.checklist_items:
                cloned_task.checklist_items.append(ChecklistItem(
                    content=item.content,
                    is_checked=False,
                    position=item.position
                ))
        
        return cloned_task
        
    def log_time(self, hours, user_id, description=None):
        """Enregistre du temps passé sur la tâche et le déduit du crédit du projet"""
        minutes = int(round(hours * 60))
        entry = TimeEntry(
            task_id=self.id,
            user_id=user_id,
            minutes=minutes,
            description=description
        )
        db.session.add(entry)
        
        # Met à jour le temps total passé sur la tâche
        if self.actual_minutes is None:
            self.actual_minutes = minutes
        else:
            self.actual_minutes += minutes
        
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

    @property
    def estimated_time(self):
        """Retourne le temps estimé en heures pour la compatibilité avec l'ancien code"""
        return self.estimated_minutes / 60 if self.estimated_minutes is not None else None
        
    @estimated_time.setter
    def estimated_time(self, value):
        """Convertit le temps estimé en minutes"""
        self.estimated_minutes = int(round(value * 60)) if value is not None else None
        
    @property
    def actual_time(self):
        """Retourne le temps réel en heures pour la compatibilité avec l'ancien code"""
        return self.actual_minutes / 60 if self.actual_minutes is not None else None
        
    @actual_time.setter
    def actual_time(self, value):
        """Convertit le temps réel en minutes"""
        self.actual_minutes = int(round(value * 60)) if value is not None else None
    
    def archive(self):
        """Archive la tâche"""
        self.is_archived = True
        self.archived_at = datetime.utcnow()
        
        # S'assurer que completed_at est défini pour les tâches terminées
        if self.status == 'terminé' and not self.completed_at:
            self.completed_at = self.updated_at
        
        db.session.commit()
    
    def unarchive(self):
        """Désarchive la tâche"""
        self.is_archived = False
        self.archived_at = None
        db.session.commit()
    
    @staticmethod
    def should_be_archived():
        """Retourne les tâches qui devraient être archivées (terminées depuis plus de 2 semaines)"""
        from datetime import timedelta
        two_weeks_ago = datetime.utcnow() - timedelta(weeks=2)
        
        # Utiliser completed_at si disponible, sinon updated_at comme fallback
        # Cela gère les cas où des tâches ont été marquées comme terminées avant l'implémentation de completed_at
        return Task.query.filter(
            Task.status == 'terminé',
            Task.is_archived == False,
            db.or_(
                db.and_(Task.completed_at.isnot(None), Task.completed_at < two_weeks_ago),
                db.and_(Task.completed_at.is_(None), Task.updated_at < two_weeks_ago)
            )
        ).all()
    
    @staticmethod
    def auto_archive_old_tasks():
        """Archive automatiquement les tâches terminées depuis plus de 2 semaines"""
        tasks_to_archive = Task.should_be_archived()
        archived_count = 0
        for task in tasks_to_archive:
            task.archive()
            archived_count += 1
        return archived_count

class TimeEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    minutes = db.Column(db.Integer, nullable=False)  # en minutes
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relation
    user = db.relationship('User', backref='time_entries', lazy=True)
    
    def __repr__(self):
        return f"TimeEntry(Task: {self.task_id}, User: {self.user.name}, Minutes: {self.minutes})"
    
    @property
    def hours(self):
        """Retourne le temps en heures pour la compatibilité avec l'ancien code"""
        return self.minutes / 60

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    _content = db.Column('content', EncryptedType, nullable=False)  # Contenu chiffré (nom interne)
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
    
    @property
    def content(self):
        """Propriété pour accéder au contenu déchiffré"""
        if not self._content or not isinstance(self._content, str) or not self._content.startswith('gAAA'):
            return self._content
            
        try:
            key = current_app.config.get('ENCRYPTION_KEY')
            if not key:
                return "[Erreur: Clé de chiffrement manquante]"
            f = Fernet(key)
            return f.decrypt(self._content.encode('utf-8')).decode('utf-8')
        except Exception as e:
            current_app.logger.error(f"Erreur lors du déchiffrement d'un commentaire: {e}")
            return "[Erreur de déchiffrement]"
    
    @content.setter
    def content(self, value):
        """Setter pour chiffrer automatiquement le contenu"""
        if value is None:
            self._content = None
        else:
            # Le chiffrement se fait automatiquement via EncryptedType
            self._content = value

class UserPinnedTask(db.Model):
    __tablename__ = 'user_pinned_task'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)