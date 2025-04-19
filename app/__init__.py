from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import config
from datetime import datetime, timezone

# Initialisation des extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "info"
bcrypt = Bcrypt()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialisation des extensions avec l'app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    
    # Contexte global pour les templates
    @app.context_processor
    def inject_now():
        return {'now': datetime.now(timezone.utc)}
    
    # Filtre pour formater les nombres à la française (avec virgule)
    @app.template_filter('fr_number')
    def fr_number_filter(value):
        """Formate un nombre avec une virgule décimale à la française"""
        if value is None:
            return ""
        return str(value).replace('.', ',')
    
    # Enregistrement des blueprints
    from app.routes.auth import auth
    from app.routes.clients import clients
    from app.routes.projects import projects
    from app.routes.tasks import tasks
    from app.routes.main import main
    
    app.register_blueprint(auth)
    app.register_blueprint(clients)
    app.register_blueprint(projects)
    app.register_blueprint(tasks)
    app.register_blueprint(main)
    
    return app