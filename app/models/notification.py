from app import db

class NotificationPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Types de notifications
    task_status_change = db.Column(db.Boolean, default=True)
    task_comment_added = db.Column(db.Boolean, default=True)
    task_time_logged = db.Column(db.Boolean, default=True)
    project_credit_low = db.Column(db.Boolean, default=True)
    
    # Préférences générales
    email_notifications_enabled = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f"NotificationPreference(user_id={self.user_id}, enabled={self.email_notifications_enabled})"