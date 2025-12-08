from app import db
from datetime import datetime
from app.utils.slug_utils import update_slug

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    initial_credit = db.Column(db.Integer, nullable=False, default=0)  # en minutes
    remaining_credit = db.Column(db.Integer, nullable=False, default=0)  # en minutes
    time_tracking_enabled = db.Column(db.Boolean, nullable=True, default=True)  # Indique si le projet utilise la gestion de temps
    is_favorite = db.Column(db.Boolean, nullable=False, default=False)  # Indique si le projet est en favori
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Clé étrangère
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    
    # Relations
    tasks = db.relationship('Task', backref='project', lazy=True, cascade='all, delete-orphan')
    credit_logs = db.relationship('CreditLog', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"Project('{self.name}', Client: '{self.client.name}', Credit: {self.remaining_credit}min)"
    
    def __init__(self, **kwargs):
        super(Project, self).__init__(**kwargs)
        if self.name and not self.slug:
            update_slug(self)
    
    def save(self):
        """Sauvegarde l'instance et met à jour le slug si nécessaire"""
        if self.name and (not self.slug or self.name != self.slug):
            update_slug(self)
        db.session.add(self)
        db.session.commit()
        
    credit_alert_sent = db.Column(db.Boolean, default=False)

    def add_credit(self, amount, note=None):
        """Ajoute du crédit au projet et crée une entrée dans l'historique"""
        # Si le projet n'utilise pas la gestion de temps, on ne fait rien
        if not self.time_tracking_enabled:
            return
            
        # Convertir les heures en minutes
        amount_minutes = int(round(amount * 60))
        
        # Met à jour le crédit restant
        self.remaining_credit += amount_minutes
        
        # Réinitialiser l'état d'alerte si le crédit est suffisant
        threshold = 120  # 2 heures en minutes
        if self.credit_alert_sent and self.remaining_credit >= threshold:
            self.credit_alert_sent = False
        
        # Ne pas ajouter de log ici si le projet n'a pas encore d'ID
        if self.id is None:
            return
            
        # Crée une entrée dans l'historique
        log = CreditLog(
            project_id=self.id,
            amount=amount_minutes,
            note=note or f"Ajout de {amount}h de crédit"
        )
        db.session.add(log)
            
    def deduct_credit(self, amount, task_id=None, note=None):
        """Déduit du crédit du projet et crée une entrée dans l'historique"""
        # Si le projet n'utilise pas la gestion de temps, on ne fait rien
        if not self.time_tracking_enabled:
            return
            
        # Convertir les heures en minutes
        amount_minutes = int(round(amount * 60))
        
        # Déduire le crédit
        self.remaining_credit -= amount_minutes
        
        # Créer l'entrée dans l'historique
        log = CreditLog(
            project_id=self.id,
            amount=-amount_minutes,
            task_id=task_id,
            note=note or f"Déduction de {amount}h de crédit"
        )
        db.session.add(log)
        
        # Vérifier si le crédit est passé sous le seuil et envoyer une alerte si nécessaire
        threshold = 120  # 2 heures en minutes
        
        # Seulement si on n'a pas déjà envoyé d'alerte pour ce passage sous le seuil
        if self.remaining_credit < threshold and not self.credit_alert_sent:
            # Marquer l'alerte comme envoyée
            self.credit_alert_sent = True
            
            # Import ici pour éviter les imports circulaires
            # Flask-Mail a besoin du contexte d'application
            from app.utils.email import send_low_credit_notification
            from flask import current_app
            
            # Vérifier si on est dans un contexte d'application (pour les tests)
            if current_app:
                # Utilisation d'un thread pour éviter de bloquer la requête
                from threading import Thread
                thread = Thread(target=send_low_credit_notification, args=(self,))
                thread.start()


class CreditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)  # Peut être positif (ajout) ou négatif (déduction)
    note = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    task = db.relationship('Task', backref='credit_logs', lazy=True)
    
    def __repr__(self):
        return f"CreditLog(Project: {self.project_id}, Amount: {self.amount}h, Date: {self.created_at})"