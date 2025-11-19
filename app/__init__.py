from flask import Flask, g, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect
from config import config
from datetime import datetime, timezone
from flask_mail import Mail
from werkzeug.exceptions import HTTPException
import os
import logging
from logging.handlers import RotatingFileHandler
import click

# Import des optimisations SQLite
from app.utils.db_optimization import set_sqlite_pragma

# Import des optimisations Python 3.13
from app.utils.python313_optimizations import get_python313_info

# Initialisation des extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "info"
bcrypt = Bcrypt()
mail = Mail()
cache = Cache()
csrf = CSRFProtect()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Monkey patch désactivé temporairement
    # if not app.debug:
    #     try:
    #         from gunicorn.workers.gthread import ThreadWorker
    #         original_accept = ThreadWorker.accept
    #         
    #         def patched_accept(self, server, listener):
    #             if not self.alive:
    #                 self.log.info('gunicorn monkey-patch: ignoring accept() called when alive==False')
    #                 return
    #             original_accept(self, server, listener)
    #         
    #         ThreadWorker.accept = patched_accept
    #     except ImportError:
    #         pass  # Gunicorn pas disponible en développement
    
    # Ajouter FLASK_ENV à la configuration de l'application
    app.config['FLASK_ENV'] = os.environ.get('FLASK_ENV', config_name)
    
    # Configuration des logs
    if not app.debug and not app.testing:
        # Créer le répertoire logs s'il n'existe pas
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Configuration du handler de fichier avec rotation
        file_handler = RotatingFileHandler('logs/chronotrak.log', maxBytes=10240000, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('ChronoTrak startup')
        
        # Démarrer le worker email pour le traitement asynchrone
        try:
            from app.utils.email import start_email_worker
            start_email_worker()
        except Exception as e:
            app.logger.error(f"Erreur lors du démarrage du worker email: {e}")

    # Configuration de sécurité
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 heure
    
    # Configuration de CSRF pour les requêtes AJAX
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_HEADERS'] = ['X-CSRF-Token']
    
    # Initialiser les extensions avec l'app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Configuration du pool de connexions pour éviter les timeouts
    with app.app_context():
        from sqlalchemy import event
        from sqlalchemy.pool import QueuePool
        
        # Configuration du pool de connexions
        engine = db.engine
        engine.pool._recycle = 3600  # Recycle les connexions après 1h
        engine.pool._pre_ping = True  # Test les connexions avant utilisation
        engine.pool._pool_size = 10   # Taille du pool
        engine.pool._max_overflow = 20  # Connexions supplémentaires
    login_manager.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    csrf.init_app(app)
    
    # Importer ici pour éviter les imports circulaires
    from app.utils.page_timer import start_timer, get_elapsed_time, log_request_time
    from app.utils.version import get_version, get_build_info
    from app.utils.error_handler import send_error_email
    
    # Middleware pour les en-têtes de sécurité
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self' https://*.cloudflare.com https://*.cloudflareinsights.com; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://cdn.jsdelivr.net https://code.jquery.com https://*.cloudflare.com https://*.cloudflareinsights.com; "
            "style-src 'self' 'unsafe-inline' "
            "https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://*.cloudflare.com https://*.cloudflareinsights.com; "
            "frame-src 'self' https://*.cloudflare.com; "
            "worker-src 'self'"
        )
        # Configuration CORS sécurisée - uniquement pour les domaines autorisés
        origin = request.headers.get('Origin')
        allowed_origins = [
            'https://chronotrak.com',
            'https://www.chronotrak.com',
            'https://app.chronotrak.com'
        ]
        
        # En développement, autoriser localhost
        if app.config.get('FLASK_ENV') == 'development':
            allowed_origins.extend([
                'http://localhost:5000',
                'http://127.0.0.1:5000',
                'http://localhost:3000',
                'http://127.0.0.1:3000'
            ])
        
        if origin and origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRF-Token'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response

    # Middleware pour mesurer le temps de chargement
    @app.before_request
    def before_request():
        start_timer()
        
        # Timeout global pour éviter les requêtes qui traînent (uniquement en production)
        if not app.debug:
            import signal
            import threading
            
            # Vérifier qu'on est dans le thread principal
            if threading.current_thread() is threading.main_thread():
                def timeout_handler(signum, frame):
                    raise TimeoutError("Request timeout")
                
                # Timeout de 30 secondes par requête
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(30)
    
    @app.after_request
    def after_request(response):
        # Annuler le timeout (uniquement en production)
        if not app.debug:
            import signal
            import threading
            
            # Vérifier qu'on est dans le thread principal
            if threading.current_thread() is threading.main_thread():
                signal.alarm(0)
        
        g.response_status_code = response.status_code
        elapsed_time = log_request_time()
        
        # Récupérer l'IP réelle du client (avec Cloudflare + reverse proxy)
        def get_real_ip():
            # Priorité aux headers Cloudflare
            headers_to_check = [
                'CF-Connecting-IP',  # Cloudflare - IP réelle du client
                'X-Real-IP',         # Nginx standard
                'X-Forwarded-For',   # Standard reverse proxy
                'X-Client-IP',       # Autres proxies
                'X-Forwarded',       # RFC 7239
                'Forwarded-For',     # RFC 7239
                'Forwarded'          # RFC 7239
            ]
            
            for header in headers_to_check:
                ip = request.headers.get(header)
                if ip:
                    # X-Forwarded-For peut contenir plusieurs IPs (client, proxy1, proxy2)
                    # On prend la première (IP du client original)
                    return ip.split(',')[0].strip()
            
            # Fallback sur l'IP directe
            return request.remote_addr
        
        client_ip = get_real_ip()
        
        # Log des requêtes lentes (> 2 secondes)
        if elapsed_time > 2.0:
            app.logger.warning(f'Slow request: {request.method} {request.url} took {elapsed_time:.2f}s from {client_ip}')
        
        # Log des requêtes très lentes (> 5 secondes) - CRITIQUE
        if elapsed_time > 5.0:
            app.logger.error(f'CRITICAL: Very slow request: {request.method} {request.url} took {elapsed_time:.2f}s from {client_ip}')
        
        # Log des erreurs 5xx
        if response.status_code >= 500:
            app.logger.error(f'Server error {response.status_code}: {request.method} {request.url} from {client_ip}')
        
        # Log des erreurs 502 spécifiquement
        if response.status_code == 502:
            app.logger.error(f'502 Bad Gateway: {request.method} {request.url} from {client_ip} - Possible timeout or worker issue')
        
        # Log de toutes les requêtes avec IP (pour debug)
        app.logger.info(f'Request: {request.method} {request.url} {response.status_code} {elapsed_time:.2f}s from {client_ip}')
        
        # Monitoring de la queue d'emails
        try:
            from app.utils.email import email_queue
            queue_size = email_queue.qsize()
            if queue_size > 50:
                app.logger.warning(f'Email queue size: {queue_size} - Possible email processing bottleneck')
        except (ImportError, AttributeError):
            # Ignorer si le module email n'est pas disponible ou si email_queue n'existe pas
            pass
        
        return response

    # Gestionnaires d'erreur
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/error.html', 
                             error_message="La page que vous recherchez n'existe pas."), 404

    @app.errorhandler(500)
    def internal_error(error):
        # Gérer les erreurs de session SQLAlchemy en faisant un rollback
        from sqlalchemy.exc import PendingRollbackError, SQLAlchemyError
        if isinstance(error, (PendingRollbackError, SQLAlchemyError)):
            try:
                db.session.rollback()
            except Exception as rollback_error:
                app.logger.error(f"Erreur lors du rollback: {rollback_error}")
        
        # Envoyer l'email d'erreur dans tous les cas
        try:
            request_info = {
                'url': request.url,
                'method': request.method,
                'ip': request.remote_addr,
                'user_agent': request.user_agent.string
            }
            send_error_email(error, request_info)
        except Exception as email_error:
            # Si l'envoi d'email échoue, on log mais on ne fait pas planter la page d'erreur
            app.logger.error(f"Échec de l'envoi d'email d'erreur: {email_error}")
        
        return render_template('errors/error.html'), 500

    @app.errorhandler(TimeoutError)
    def handle_timeout(error):
        app.logger.error(f"Timeout détecté: {error}")
        try:
            request_info = {
                'url': request.url,
                'method': request.method,
                'ip': request.remote_addr,
                'user_agent': request.user_agent.string
            }
            send_error_email(error, request_info)
        except Exception as email_error:
            app.logger.error(f"Échec de l'envoi d'email d'erreur: {email_error}")
        return render_template('errors/error.html', error_message="La requête a pris trop de temps"), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        # Gérer les erreurs HTTP
        if isinstance(error, HTTPException):
            return render_template('errors/error.html',
                                 error_message=error.description), error.code

        # Gérer les erreurs de session SQLAlchemy en faisant un rollback
        from sqlalchemy.exc import PendingRollbackError, SQLAlchemyError
        if isinstance(error, (PendingRollbackError, SQLAlchemyError)):
            try:
                db.session.rollback()
            except Exception as rollback_error:
                app.logger.error(f"Erreur lors du rollback: {rollback_error}")

        # Envoyer l'email d'erreur dans tous les cas
        try:
            request_info = {
                'url': request.url,
                'method': request.method,
                'ip': request.remote_addr,
                'user_agent': request.user_agent.string
            }
            send_error_email(error, request_info)
        except Exception as email_error:
            # Si l'envoi d'email échoue, on log mais on ne fait pas planter la page d'erreur
            app.logger.error(f"Échec de l'envoi d'email d'erreur: {email_error}")
        
        return render_template('errors/error.html'), 500
    
    # Contexte global pour les templates
    @app.context_processor
    def inject_globals():
        # Importer ici à nouveau pour éviter les erreurs d'import circulaire
        from app.utils.version import get_version, get_build_info
        from app.utils.page_timer import get_elapsed_time
        
        # Obtenir la version - s'assurer qu'elle est correcte
        version = get_version()
        
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
        elif '/tasks/' in current_path or current_path == '/my-tasks':
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
    
    # Filtre pour gérer les comparaisons avec None
    @app.template_filter('safe_compare')
    def safe_compare_filter(value, operator, threshold):
        """Compare une valeur avec un seuil en gérant les cas None"""
        if value is None:
            return False
        try:
            if operator == '<':
                return value < threshold
            elif operator == '>':
                return value > threshold
            elif operator == '<=':
                return value <= threshold
            elif operator == '>=':
                return value >= threshold
            elif operator == '==':
                return value == threshold
            else:
                return False
        except (TypeError, ValueError):
            return False
    
    # Filtre pour gérer les valeurs None
    @app.template_filter('default_if_none')
    def default_if_none_filter(value, default=0):
        """Retourne une valeur par défaut si la valeur est None"""
        return value if value is not None else default
    
    # Configuration de CSRF pour les requêtes AJAX
    @csrf.exempt
    def csrf_exempt():
        return True
    
    # Enregistrement des blueprints
    from app.routes.auth import auth
    from app.routes.clients import clients
    from app.routes.projects import projects
    from app.routes.tasks import tasks
    from app.routes.main import main
    from app.routes.admin import admin
    from app.routes.communications import communications
    from app.routes.api import api
    from app.routes.optimization import optimization
    
    app.register_blueprint(auth)
    app.register_blueprint(clients)
    app.register_blueprint(projects)
    app.register_blueprint(tasks)
    app.register_blueprint(main)
    app.register_blueprint(admin)
    app.register_blueprint(communications)
    app.register_blueprint(api)
    app.register_blueprint(optimization)
    
    # Route pour le favicon
    @app.route('/favicon.ico')
    def favicon():
        """Serve le favicon"""
        from flask import send_from_directory
        return send_from_directory(
            app.static_folder, 
            'favicon/favicon.ico', 
            mimetype='image/vnd.microsoft.icon'
        )

    # Route de santé pour monitoring
    @app.route('/health')
    def health_check():
        """Endpoint de santé pour monitoring"""
        try:
            # Vérifier la base de données avec la syntaxe correcte
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            
            # Vérifier la queue d'emails
            from app.utils.email import email_queue
            queue_size = email_queue.qsize()
            
            # Vérifier l'état du worker email
            from app.utils.email import email_worker_thread
            worker_alive = email_worker_thread and email_worker_thread.is_alive()
            
            return {
                'status': 'healthy',
                'database': 'ok',
                'email_queue_size': queue_size,
                'email_worker_alive': worker_alive,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            app.logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }, 500

    # Commandes CLI
    @app.cli.command()
    @click.option('--force', is_flag=True, help='Forcer l\'archivage même en environnement de développement')
    def auto_archive(force):
        """Archive automatiquement les tâches terminées depuis plus de 2 semaines"""
        import os
        
        # Vérifier que nous sommes en production ou que le mode force est activé
        flask_env = os.environ.get('FLASK_ENV', 'development')
        app_env = app.config.get('FLASK_ENV', 'development')
        
        # Utiliser l'environnement de l'application si disponible, sinon celui de l'OS
        current_env = app_env if app_env != 'development' else flask_env
        
        if current_env != 'production' and not force:
            print(f"Archivage automatique désactivé en environnement '{current_env}'. Seul l'environnement 'production' permet l'archivage automatique.")
            print(f"Variables détectées - FLASK_ENV: {flask_env}, App config: {app_env}")
            print(f"Pour forcer l'archivage en développement, utilisez: flask auto-archive --force")
            return
        
        if force and current_env != 'production':
            print(f"⚠️  Mode FORCE activé - Archivage en environnement '{current_env}' (normalement réservé à la production)")
        
        from app.models.task import Task
        
        tasks_to_archive = Task.should_be_archived()
        
        if not tasks_to_archive:
            print("Aucune tâche à archiver.")
            return
        
        print(f"{len(tasks_to_archive)} tâche(s) à archiver...")
        
        archived_count = 0
        for task in tasks_to_archive:
            try:
                task.archive()
                archived_count += 1
                print(f"  ✓ Archivée: {task.title} (Projet: {task.project.name})")
            except Exception as e:
                print(f"  ✗ Erreur lors de l'archivage de '{task.title}': {e}")
        
        print(f"{archived_count} tâche(s) archivée(s) avec succès.")
    
    return app