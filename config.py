import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'You-Cant-Guess-This'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///chronotrak.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}