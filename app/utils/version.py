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
    Accepte les formats avec ou sans préfixe "v".
    """
    try:
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, 'r') as f:
                version = f.read().strip()
                
                # Debug: Afficher la version lue pour diagnostiquer les problèmes
                print(f"Version lue depuis le fichier: '{version}'")
                
                # Accepter à la fois v1.2.3 et 1.2.3 comme formats valides
                if version:
                    if re.match(r'^v?\d+\.\d+\.\d+$', version):
                        return version
                    else:
                        print(f"Format de version non reconnu: '{version}'")
                else:
                    print("Fichier VERSION vide ou illisible")
    except Exception as e:
        import traceback
        print(f"Erreur lors de la lecture du fichier de version: {e}")
        print(traceback.format_exc())
        if current_app:
            current_app.logger.error(f"Erreur lors de la lecture du fichier de version: {e}")
    
    # Version par défaut
    return "dev"

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