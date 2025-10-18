#!/usr/bin/env python3
"""
Script pour archiver automatiquement les tâches terminées depuis plus de 2 semaines.
Ce script peut être exécuté via cron pour automatiser l'archivage.
"""

import sys
import os
from datetime import datetime

# Ajouter le répertoire parent au path pour importer l'application
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.task import Task

def main():
    """Fonction principale pour l'archivage automatique"""
    # Vérifier que nous sommes en production
    flask_env = os.environ.get('FLASK_ENV', 'development')
    if flask_env != 'production':
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Archivage automatique désactivé en environnement '{flask_env}'. Seul l'environnement 'production' permet l'archivage automatique.")
        return
    
    app = create_app()
    
    with app.app_context():
        try:
            # Récupérer les tâches qui devraient être archivées
            tasks_to_archive = Task.should_be_archived()
            
            if not tasks_to_archive:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Aucune tâche à archiver.")
                return
            
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {len(tasks_to_archive)} tâche(s) à archiver...")
            
            # Archiver les tâches
            archived_count = 0
            for task in tasks_to_archive:
                try:
                    task.archive()
                    archived_count += 1
                    print(f"  ✓ Archivée: {task.title} (Projet: {task.project.name})")
                except Exception as e:
                    print(f"  ✗ Erreur lors de l'archivage de '{task.title}': {e}")
            
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {archived_count} tâche(s) archivée(s) avec succès.")
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de l'archivage automatique: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()
