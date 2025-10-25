# Configuration Gunicorn ultra-robuste pour ChronoTrak
import multiprocessing
import os

# Configuration de base
bind = "0.0.0.0:5000"
workers = 2  # Réduit pour éviter les conflits
worker_class = "sync"
worker_connections = 1000

# Timeouts optimisés
timeout = 30
keepalive = 5
graceful_timeout = 30

# Gestion des workers
max_requests = 100  # Redémarre les workers après 100 requêtes
max_requests_jitter = 10
preload_app = True

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Gestion des erreurs
capture_output = True
enable_stdio_inheritance = True

# Configuration pour la robustesse
def when_ready(server):
    """Callback quand le serveur est prêt"""
    server.log.info("ChronoTrak Gunicorn server ready")

def worker_int(worker):
    """Callback quand un worker est interrompu"""
    worker.log.info("Worker %s interrupted", worker.pid)

def pre_fork(server, worker):
    """Callback avant le fork d'un worker"""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    """Callback après le fork d'un worker"""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def worker_abort(worker):
    """Callback quand un worker est abandonné"""
    worker.log.info("Worker %s aborted", worker.pid)

# Configuration des limites
worker_tmp_dir = "/dev/shm"  # Utilise la RAM pour les fichiers temporaires

# Variables d'environnement pour la robustesse
raw_env = [
    'PYTHONUNBUFFERED=1',
    'PYTHONDONTWRITEBYTECODE=1',
    'PYTHONHASHSEED=random',
]
