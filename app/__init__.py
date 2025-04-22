from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import config
from datetime import datetime, timezone
from flask_mail import Mail

# Initialisation des extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "info"
bcrypt = Bcrypt()
mail = Mail()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialiser Mail
    mail.init_app(app)
    
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
    
    # Gestion du background du header
    @app.template_filter('nav_bg_color')
    def nav_bg_color_filter(current_path):
        """Détermine la couleur de fond de la navbar en fonction de l'URL actuelle"""
        if '/clients/' in current_path or current_path == '/clients':
            return 'bg-primary'
        elif '/projects/' in current_path or current_path == '/projects':
            return 'bg-success'
        elif '/tasks/' in current_path or current_path == '/my_tasks':
            return 'bg-info'
        elif '/reports' in current_path:
            return 'bg-reports'
        else:
            # Page par défaut (dashboard)
            return 'bg-secondary'
    
    # Enregistrement des blueprints
    from app.routes.auth import auth
    from app.routes.clients import clients
    from app.routes.projects import projects
    from app.routes.tasks import tasks
    from app.routes.main import main
    from app.routes.admin import admin
    
    app.register_blueprint(auth)
    app.register_blueprint(clients)
    app.register_blueprint(projects)
    app.register_blueprint(tasks)
    app.register_blueprint(main)
    app.register_blueprint(admin)
    
    return app