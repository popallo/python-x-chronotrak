# Configuration Gunicorn ultra-robuste pour ChronoTrak avec SQLite
import multiprocessing
import os

# Configuration de base
bind = "0.0.0.0:5000"
workers = 1  # CRITIQUE: 1 seul worker pour SQLite (pas thread-safe)
worker_class = "sync"
worker_connections = 1000

# Timeouts optimisés pour SQLite
timeout = 60  # Augmenté pour les requêtes SQLite
keepalive = 10
graceful_timeout = 60

# Gestion des workers - Désactivé à cause du bug Gunicorn 21.0.0+
# max_requests = 50  # BUG: Cause des 502 avec Gunicorn 21.0.0+
# max_requests_jitter = 10
preload_app = True

# Logging détaillé
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Gestion des erreurs
capture_output = True
enable_stdio_inheritance = True

# Configuration pour la robustesse SQLite
def when_ready(server):
    """Callback quand le serveur est prêt"""
    server.log.info("ChronoTrak Gunicorn server ready with SQLite optimization")

def worker_int(worker):
    """Callback quand un worker est interrompu"""
    worker.log.info("Worker %s interrupted", worker.pid)

def pre_fork(server, worker):
    """Callback avant le fork d'un worker"""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    """Callback après le fork d'un worker - Configuration SQLite"""
    server.log.info("Worker spawned (pid: %s) - SQLite optimized", worker.pid)
    
    # Configuration SQLite pour le worker
    import os
    os.environ['SQLITE_THREADSAFE'] = '1'
    os.environ['SQLITE_SYNCHRONOUS'] = 'NORMAL'

def worker_abort(worker):
    """Callback quand un worker est abandonné"""
    worker.log.info("Worker %s aborted", worker.pid)

# Configuration des limites pour SQLite
worker_tmp_dir = "/dev/shm"  # Utilise la RAM pour les fichiers temporaires

# Variables d'environnement pour la robustesse SQLite
raw_env = [
    'PYTHONUNBUFFERED=1',
    'PYTHONDONTWRITEBYTECODE=1',
    'PYTHONHASHSEED=random',
    'SQLITE_THREADSAFE=1',
    'SQLITE_SYNCHRONOUS=NORMAL',
    'SQLITE_CACHE_SIZE=10000',
    'SQLITE_TEMP_STORE=MEMORY',
]

# Configuration spécifique SQLite
def on_starting(server):
    """Callback au démarrage du serveur"""
    server.log.info("Starting ChronoTrak with SQLite optimization")
    server.log.info("Workers: %d (SQLite requires single worker)", workers)
    server.log.info("Timeout: %ds (optimized for SQLite)", timeout)
