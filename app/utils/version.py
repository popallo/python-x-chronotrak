"""
Module de gestion de version pour l'application ChronoTrak.
"""
import os
import re
from datetime import datetime
from pathlib import Path
from flask import current_app

# Chemin vers le fichier de version
VERSION_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'VERSION')

def get_version():
    """
    Récupère la version actuelle de l'application.
    Renvoie la version depuis le fichier VERSION ou "dev" si le fichier n'existe pas.
    """
    try:
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, 'r') as f:
                version = f.read().strip()
                # Valider le format de version x.y.z
                if re.match(r'^\d+\.\d+\.\d+$', version):
                    return version
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la lecture du fichier de version: {e}")
    
    # Version par défaut en développement
    return "1.0.0-dev"

def get_build_info():
    """
    Récupère les informations de build (date, environnement).
    """
    build_info = {}
    
    # Date de build - par défaut la date de modification du fichier VERSION
    try:
        if os.path.exists(VERSION_FILE):
            build_date = datetime.fromtimestamp(os.path.getmtime(VERSION_FILE))
            build_info['date'] = build_date.strftime('%Y-%m-%d')
        else:
            build_info['date'] = datetime.now().strftime('%Y-%m-%d')
    except Exception:
        build_info['date'] = "N/A"
    
    # Environnement
    build_info['env'] = os.environ.get('FLASK_ENV', 'development')
    
    return build_info