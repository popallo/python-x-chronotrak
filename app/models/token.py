import uuid
from datetime import timedelta

from app import db
from app.utils import get_utc_now


class PasswordResetToken(db.Model):
    """Modèle pour les jetons de réinitialisation de mot de passe"""

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)

    # Relation avec l'utilisateur
    user = db.relationship("User", backref=db.backref("reset_tokens", lazy=True))

    def __init__(self, user_id, expires_in=24):
        """
        Initialise un nouveau jeton de réinitialisation

        :param user_id: ID de l'utilisateur concerné
        :param expires_in: Durée de validité en heures (par défaut 24h)
        """
        self.user_id = user_id
        self.token = str(uuid.uuid4())
        # Convertir en datetime naive pour SQLite
        self.created_at = get_utc_now().replace(tzinfo=None)
        self.expires_at = self.created_at + timedelta(hours=expires_in)
        self.is_used = False

    def is_valid(self):
        """Vérifie si le jeton est valide (non expiré et non utilisé)"""
        # Retirer le fuseau horaire de get_utc_now()
        now = get_utc_now().replace(tzinfo=None)
        return not self.is_used and self.expires_at > now

    def mark_as_used(self):
        """Marque le jeton comme utilisé"""
        self.is_used = True
        db.session.commit()

    @classmethod
    def get_valid_token(cls, token_string):
        """Récupère un jeton valide à partir de sa chaîne"""
        token = cls.query.filter_by(token=token_string).first()
        if token and token.is_valid():
            return token
        return None

    @classmethod
    def generate_for_user(cls, user_id, expires_in=24):
        """Génère un nouveau jeton pour un utilisateur"""
        # Invalider tous les jetons existants pour cet utilisateur
        existing_tokens = cls.query.filter_by(user_id=user_id, is_used=False).all()
        for token in existing_tokens:
            token.is_used = True

        # Créer un nouveau jeton
        new_token = cls(user_id=user_id, expires_in=expires_in)

        # Sauvegarder dans la base de données
        db.session.add(new_token)
        db.session.commit()

        return new_token
