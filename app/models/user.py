from app import db, bcrypt, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='technicien')  # admin ou technicien
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    assigned_tasks = db.relationship('Task', backref='assigned_to', lazy=True)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
        
    def is_admin(self):
        return self.role == 'admin'
        
    def __repr__(self):
        return f"User('{self.name}', '{self.email}', '{self.role}')"