from app import db
from datetime import datetime

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
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
        
    def add_credit(self, amount, note=None):
        """Ajoute du crédit au projet et crée une entrée dans l'historique"""
        # Met à jour le crédit restant
        self.remaining_credit += amount
        
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
            
    def deduct_credit(self, amount, task_id=None):
        """Déduit du crédit du projet et crée une entrée dans l'historique"""
        self.remaining_credit -= amount
        
        log = CreditLog(
            project_id=self.id,
            amount=-amount,
            task_id=task_id,
            note=f"Déduction de {amount}h de crédit"
        )
        db.session.add(log)

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
    
    def __repr__(self):
        return f"CreditLog(Project: {self.project_id}, Amount: {self.amount}h, Date: {self.created_at})"