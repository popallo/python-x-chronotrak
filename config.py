import os
from dotenv import load_dotenv
import base64
from cryptography.fernet import Fernet

load_dotenv(override=True)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///chronotrak.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuration du pool de connexions et timeouts pour SQLite
    # ATTENTION: SQLite n'est PAS thread-safe avec plusieurs workers Gunicorn
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'timeout': 30,
            'check_same_thread': False,  # False pour le développement, True pour la production
            'isolation_level': None     # Mode autocommit pour éviter les deadlocks
        }
    }
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    CREDIT_THRESHOLD = int(os.environ.get('CREDIT_THRESHOLD', '2'))
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    MAIL_SUBJECT_PREFIX = '[ChronoTrak]'
    MAIL_SENDER = 'ChronoTrak Admin <admin@chronotrak.com>'
    ADMIN = os.environ.get('ADMIN')
    
    # Cloudflare Turnstile
    TURNSTILE_SITE_KEY = os.environ.get('TURNSTILE_SITE_KEY')
    TURNSTILE_SECRET_KEY = os.environ.get('TURNSTILE_SECRET_KEY')
    TURNSTILE_ENABLED = os.environ.get('TURNSTILE_ENABLED', 'false').lower() in ['true', 'on', '1']
    
    # Clé de chiffrement pour les données sensibles
    # ATTENTION: ENCRYPTION_KEY DOIT être définie dans les variables d'environnement
    # Si la clé change, les données existantes ne pourront plus être déchiffrées
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
    if not ENCRYPTION_KEY:
        raise ValueError("ENCRYPTION_KEY doit être définie dans les variables d'environnement. "
                        "Générez une clé avec: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'")

    # Configuration du cache
    CACHE_TYPE = 'SimpleCache'  # Utilise le cache en mémoire
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes par défaut
    CACHE_THRESHOLD = 1000  # Nombre maximum d'éléments dans le cache
    CACHE_KEY_PREFIX = 'chronotrak_'  # Préfixe pour les clés de cache

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'

class ProductionConfig(Config):
    DEBUG = False
    
    # Configuration SQLite spécifique à la production
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'timeout': 30,
            'check_same_thread': True,  # True en production pour la sécurité
            'isolation_level': None
        }
    }
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