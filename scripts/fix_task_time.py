#!/usr/bin/env python
"""
Script pour corriger le temps d'une tâche spécifique et 
ajuster le crédit du projet en conséquence.

Usage:
  python fix_task_time.py <task_id> <new_time_in_hours>

Exemple:
  python fix_task_time.py 5 0.1667  # Pour définir 10 minutes exactement
"""

import sys
import os
from datetime import datetime, timezone

# Déterminer le chemin absolu du répertoire racine de l'application
# Le script est supposé être dans scripts/ qui est dans le répertoire racine
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)  # Remonter d'un niveau

# Ajouter le répertoire racine au chemin de recherche Python
sys.path.insert(0, root_dir)

try:
    from app import create_app, db
    from app.models.task import Task, TimeEntry
    from app.models.project import Project, CreditLog
except ImportError as e:
    print(f"Erreur d'importation: {e}")
    print(f"Vérifiez que vous exécutez ce script depuis le répertoire racine du projet.")
    print(f"Chemin racine actuel: {root_dir}")
    sys.exit(1)

def get_utc_now():
    """Renvoie la date et l'heure actuelle en UTC avec fuseau horaire explicite"""
    return datetime.now(timezone.utc)

def fix_task_time(task_id, new_time):
    """Corrige le temps d'une tâche et ajuste le crédit du projet associé."""
    # Détecter l'environnement à partir d'une variable d'env ou utiliser development par défaut
    env = os.environ.get('FLASK_ENV', 'development')
    app = create_app(env)
    
    with app.app_context():
        # Récupérer la tâche
        task = Task.query.get(task_id)
        if not task:
            print(f"Erreur: Tâche avec ID {task_id} non trouvée.")
            return False
        
        # Récupérer le projet
        project = task.project
        if not project:
            print(f"Erreur: Projet associé à la tâche {task_id} non trouvé.")
            return False
        
        # Calculer la différence de temps
        old_time = task.actual_time or 0
        time_difference = new_time - old_time
        
        print(f"Tâche: {task.title} (ID: {task.id})")
        print(f"Projet: {project.name} (ID: {project.id})")
        print(f"Temps actuel: {old_time:.4f} heures ({old_time * 60:.2f} minutes)")
        print(f"Nouveau temps: {new_time:.4f} heures ({new_time * 60:.2f} minutes)")
        print(f"Différence: {time_difference:.4f} heures ({time_difference * 60:.2f} minutes)")
        print(f"Crédit actuel du projet: {project.remaining_credit:.4f} heures")
        
        # Demander confirmation
        confirm = input("\nConfirmez-vous cette modification? (y/n): ")
        if confirm.lower() != 'y':
            print("Opération annulée.")
            return False
        
        # Mettre à jour le temps de la tâche
        task.actual_time = new_time
        
        # Ajuster le crédit du projet
        # Si time_difference est positif, on réduit le crédit
        # Si time_difference est négatif, on augmente le crédit
        project.remaining_credit -= time_difference
        
        # Créer une entrée dans l'historique des crédits
        if time_difference != 0:
            log_note = "Correction manuelle de temps de tâche"
            credit_log = CreditLog(
                project_id=project.id,
                task_id=task.id,
                amount=-time_difference,  # Négatif car on ajuste le crédit dans le sens inverse
                note=log_note,
                created_at=get_utc_now()
            )
            db.session.add(credit_log)
        
        # Vérifier s'il y a des entrées de temps associées à mettre à jour
        time_entries = TimeEntry.query.filter_by(task_id=task.id).all()
        if time_entries:
            print(f"\nAttention: {len(time_entries)} entrée(s) de temps trouvée(s) pour cette tâche.")
            print("Ce script ne modifie pas les entrées de temps individuelles.")
            print("Si nécessaire, vous devrez les ajuster manuellement.")
        
        # Enregistrer les modifications
        db.session.commit()
        
        print("\nModification effectuée avec succès!")
        print(f"Nouveau temps de la tâche: {task.actual_time:.4f} heures ({task.actual_time * 60:.2f} minutes)")
        print(f"Nouveau crédit du projet: {project.remaining_credit:.4f} heures")
        
        return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <task_id> <new_time_in_hours>")
        print("Exemple: python fix_task_time.py 5 0.1667  # Pour définir 10 minutes exactement")
        sys.exit(1)
    
    try:
        task_id = int(sys.argv[1])
        new_time = float(sys.argv[2])
    except ValueError:
        print("Erreur: L'ID de tâche doit être un entier et le nouveau temps un nombre décimal.")
        sys.exit(1)
    
    if new_time < 0:
        print("Erreur: Le nouveau temps ne peut pas être négatif.")
        sys.exit(1)
    
    if fix_task_time(task_id, new_time):
        sys.exit(0)
    else:
        sys.exit(1)