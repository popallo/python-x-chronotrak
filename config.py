import os
from dotenv import load_dotenv
import base64

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'You-Cant-Guess-This'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///chronotrak.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    CREDIT_THRESHOLD = 2  # Seuil de crédit pour les alertes
    
    # Clé de chiffrement pour les données sensibles
    # Si non définie dans les variables d'environnement, une clé temporaire sera générée
    # ATTENTION: Si la clé change, les données existantes ne pourront plus être déchiffrées
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
    if not ENCRYPTION_KEY:
        # Générer une clé temporaire (pour le développement uniquement)
        # En production, définissez ENCRYPTION_KEY dans les variables d'environnement
        ENCRYPTION_KEY = base64.urlsafe_b64encode(os.urandom(32))
        print("ATTENTION: Utilisation d'une clé de chiffrement temporaire. Définissez ENCRYPTION_KEY en production.")

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'

class ProductionConfig(Config):
    DEBUG = False
    # En production, la clé de chiffrement DOIT être définie dans les variables d'environnement
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        if not os.environ.get('ENCRYPTION_KEY'):
            raise ValueError("ENCRYPTION_KEY doit être définie dans les variables d'environnement en production")

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}