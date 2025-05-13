from app import db
from datetime import datetime
from app.utils.slug_utils import update_slug

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    initial_credit = db.Column(db.Float, nullable=False, default=0)  # en heures
    remaining_credit = db.Column(db.Float, nullable=False, default=0)  # en heures
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Clé étrangère
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    
    # Relations
    tasks = db.relationship('Task', backref='project', lazy=True, cascade='all, delete-orphan')
    credit_logs = db.relationship('CreditLog', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"Project('{self.name}', Client: '{self.client.name}', Credit: {self.remaining_credit}h)"
    
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
        # Arrondir le montant à 2 décimales pour éviter les erreurs de calcul
        amount = round(amount, 2)
        
        # Met à jour le crédit restant et arrondir le résultat
        self.remaining_credit = round(self.remaining_credit + amount, 2)
        
        # Réinitialiser l'état d'alerte si le crédit est suffisant
        threshold = 2  # Même seuil que dans deduct_credit
        if self.credit_alert_sent and self.remaining_credit >= threshold:
            self.credit_alert_sent = False
        
        # Ne pas ajouter de log ici si le projet n'a pas encore d'ID
        if self.id is None:
            return
            
        # Crée une entrée dans l'historique
        log = CreditLog(
            project_id=self.id,
            amount=amount,
            note=note or f"Ajout de {amount}h de crédit"
        )
        db.session.add(log)
            
    # app/models/project.py (modifiez la méthode deduct_credit)
    def deduct_credit(self, amount, task_id=None):
        """Déduit du crédit du projet et crée une entrée dans l'historique"""
        # Arrondir le montant à 4 décimales pour éviter les erreurs de précision
        amount = round(float(amount), 4)
        
        # Déduire le crédit et arrondir le résultat à 4 décimales
        self.remaining_credit = round(self.remaining_credit - amount, 4)
        
        # Créer l'entrée dans l'historique
        log = CreditLog(
            project_id=self.id,
            amount=-amount,
            task_id=task_id,
            note=f"Déduction de {amount}h de crédit"
        )
        db.session.add(log)
        
        # Vérifier si le crédit est passé sous le seuil et envoyer une alerte si nécessaire
        threshold = 2  # Seuil en heures
        
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

    def get_total_credit_allocated(self):
        """Calcule le crédit total alloué au projet au fil du temps"""
        from sqlalchemy import func
        
        # Somme de tous les montants positifs dans les logs de crédit SAUF le crédit initial
        additional_credits = db.session.query(func.sum(CreditLog.amount)).filter(
            CreditLog.project_id == self.id,
            CreditLog.amount > 0,
            ~CreditLog.note.like("Crédit initial%")  # Exclusion des logs de crédit initial
        ).scalar() or 0
        
        return self.initial_credit + additional_credits


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