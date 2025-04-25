"""
Module pour mesurer le temps de chargement des pages dans l'application.
Cette fonctionnalité permet de suivre les performances de l'application.
"""
import time
from functools import wraps
from flask import g, request
from datetime import datetime

def start_timer():
    """
    Démarrer le chronomètre pour mesurer le temps de traitement d'une requête.
    Cette fonction est appelée avant le traitement de chaque requête.
    """
    g.start_time = time.time()
    g.request_start_time = datetime.now()

def get_elapsed_time():
    """
    Calcule le temps écoulé depuis le début de la requête.
    Retourne le temps en millisecondes et en secondes formaté.
    """
    if hasattr(g, 'start_time'):
        # Calculer le temps écoulé en millisecondes
        elapsed = (time.time() - g.start_time) * 1000
        
        # Formater pour l'affichage
        if elapsed < 1:
            formatted = f"{elapsed:.3f} µs"  # Microsecondes
        elif elapsed < 1000:
            formatted = f"{elapsed:.2f} ms"  # Millisecondes
        else:
            # Convertir en secondes pour les temps plus longs
            formatted = f"{elapsed/1000:.2f} s"  # Secondes
        
        return {
            'ms': elapsed,
            'formatted': formatted
        }
    
    return {
        'ms': 0,
        'formatted': 'N/A'
    }

def log_request_time():
    """
    Enregistre le temps de traitement de la requête dans les logs.
    Cette fonction est appelée après le traitement de chaque requête.
    """
    if hasattr(g, 'start_time'):
        elapsed = get_elapsed_time()
        path = request.path
        method = request.method
        status = getattr(g, 'response_status_code', '?')
        
        # Log au format: MÉTHODE PATH STATUS TEMPSms
        from flask import current_app
        current_app.logger.info(f"Request timing: {method} {path} {status} {elapsed['formatted']}")