from app import bcrypt, db, login_manager
from app.utils import get_utc_now
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# table d'association pour la relation many-to-many entre User et Client
user_clients = db.Table(
    "user_clients",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("client_id", db.Integer, db.ForeignKey("client.id"), primary_key=True),
)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default="technicien")  # admin, technicien ou client
    created_at = db.Column(db.DateTime, default=get_utc_now)
    last_login = db.Column(db.DateTime, nullable=True)

    # Relations
    assigned_tasks = db.relationship("Task", backref="assigned_to", lazy=True)
    pinned_tasks = db.relationship(
        "Task", secondary="user_pinned_task", backref=db.backref("pinned_by_users", lazy="dynamic"), lazy="dynamic"
    )

    # Nouvelle relation pour les utilisateurs de type client
    clients = db.relationship("Client", secondary=user_clients, backref=db.backref("users", lazy=True), lazy="subquery")

    # Préférence de notification
    notification_preferences = db.relationship(
        "NotificationPreference", backref="user", uselist=False, cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == "admin"

    # Nouvelle méthode pour vérifier si l'utilisateur est un client
    def is_client(self):
        return self.role == "client"

    # Nouvelle méthode pour vérifier si l'utilisateur est un technicien
    def is_technician(self):
        return self.role == "technicien"

    # Méthode pour vérifier si l'utilisateur est associé à un client spécifique
    def has_access_to_client(self, client_id):
        if self.is_admin() or self.is_technician():
            return True
        return any(client.id == client_id for client in self.clients)

    def __repr__(self):
        return f"User('{self.name}', '{self.email}', '{self.role}')"
