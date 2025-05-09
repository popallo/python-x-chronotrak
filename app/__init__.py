from flask import Flask, g, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import config
from datetime import datetime, timezone
from flask_mail import Mail
from werkzeug.exceptions import HTTPException

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
    
    # Importer ici pour éviter les imports circulaires
    from app.utils.page_timer import start_timer, get_elapsed_time, log_request_time
    from app.utils.version import get_version, get_build_info
    from app.utils.error_handler import send_error_email
    
    # Middleware pour mesurer le temps de chargement
    @app.before_request
    def before_request():
        start_timer()
    
    @app.after_request
    def after_request(response):
        g.response_status_code = response.status_code
        log_request_time()
        return response

    # Gestionnaires d'erreur
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/error.html', 
                             error_message="La page que vous recherchez n'existe pas."), 404

    @app.errorhandler(500)
    def internal_error(error):
        # Envoyer l'email d'erreur en production
        if not app.debug:
            request_info = {
                'url': request.url,
                'method': request.method,
                'ip': request.remote_addr,
                'user_agent': request.user_agent.string
            }
            send_error_email(error, request_info)
        return render_template('errors/error.html'), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        # Gérer les erreurs HTTP
        if isinstance(error, HTTPException):
            return render_template('errors/error.html',
                                 error_message=error.description), error.code

        # Envoyer l'email d'erreur en production
        if not app.debug:
            request_info = {
                'url': request.url,
                'method': request.method,
                'ip': request.remote_addr,
                'user_agent': request.user_agent.string
            }
            send_error_email(error, request_info)
        return render_template('errors/error.html'), 500
    
    # Contexte global pour les templates
    @app.context_processor
    def inject_globals():
        # Importer ici à nouveau pour éviter les erreurs d'import circulaire
        from app.utils.version import get_version, get_build_info
        from app.utils.page_timer import get_elapsed_time
        
        # Obtenir la version - s'assurer qu'elle est correcte
        version = get_version()
        print(f"Version injectée dans le template: '{version}'")
        
        return {
            'now': datetime.now(timezone.utc),
            'version': version,
            'build_info': get_build_info(),
            'page_load': get_elapsed_time()
        }
    
    # Filtre pour formater les nombres à la française (avec virgule)
    @app.template_filter('fr_number')
    def fr_number_filter(value):
        """Formate un nombre avec une virgule décimale à la française"""
        if value is None:
            return ""
        return str(value).replace('.', ',')
    
    # Filtre pour formater les temps en heures et minutes
    from app.utils.time_format import format_time
    @app.template_filter('format_time')
    def format_time_filter(value):
        """Filtre Jinja pour formater le temps"""
        return format_time(value)
    
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
    
    # Filtre pour la couleur des badges de statut
    @app.template_filter('status_color')
    def status_color_filter(status):
        """Détermine la couleur du badge en fonction du statut de la tâche"""
        status_colors = {
            'à faire': 'info',
            'en cours': 'warning',
            'terminé': 'success'
        }
        return status_colors.get(status, 'secondary')
    
    # Filtre pour la couleur des badges de priorité
    @app.template_filter('priority_color')
    def priority_color_filter(priority):
        """Détermine la couleur du badge en fonction de la priorité de la tâche"""
        priority_colors = {
            'basse': 'secondary',
            'normale': 'primary',
            'haute': 'warning',
            'urgente': 'danger'
        }
        return priority_colors.get(priority, 'secondary')
    
    # Enregistrement des blueprints
    from app.routes.auth import auth
    from app.routes.clients import clients
    from app.routes.projects import projects
    from app.routes.tasks import tasks
    from app.routes.main import main
    from app.routes.admin import admin
    from app.routes.communications import communications
    
    app.register_blueprint(auth)
    app.register_blueprint(clients)
    app.register_blueprint(projects)
    app.register_blueprint(tasks)
    app.register_blueprint(main)
    app.register_blueprint(admin)
    app.register_blueprint(communications)
    
    return app