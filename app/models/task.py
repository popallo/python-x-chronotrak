from app import db
from datetime import datetime

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
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
    
    def __repr__(self):
        return f"Task('{self.title}', Status: '{self.status}', Project: '{self.project.name}')"
        
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