import sys
import os

# Déterminer le chemin absolu du répertoire racine de l'application
# Le script est supposé être dans scripts/ qui est dans le répertoire racine
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)  # Remonter d'un niveau

# Ajouter le répertoire racine au chemin de recherche Python
sys.path.insert(0, root_dir)

try:
    from app import create_app, db
    from app.models.project import Project
except ImportError as e:
    print(f"Erreur d'importation: {e}")
    print(f"Vérifiez que vous exécutez ce script depuis le répertoire racine du projet.")
    print(f"Chemin racine actuel: {root_dir}")
    sys.exit(1)

def convert_hours_to_minutes(hours):
    """Convertit les heures en minutes et arrondit à l'entier le plus proche"""
    return round(hours * 60)

def main():
    # Détecter l'environnement à partir d'une variable d'env ou utiliser development par défaut
    env = os.environ.get('FLASK_ENV', 'development')
    
    # Créer l'application Flask avec l'environnement spécifié
    app = create_app(env)
    
    # Liste des projets à mettre à jour avec leurs crédits initiaux et restants
    projects_data = [
        {'id': 1, 'initial': 3.9, 'remaining': 4.05},
        {'id': 2, 'initial': 3.0, 'remaining': 2.34},
        {'id': 3, 'initial': 31.1, 'remaining': 24.43},
        {'id': 4, 'initial': 2.8, 'remaining': 1.0},
        {'id': 5, 'initial': 2.0, 'remaining': 1.0}
    ]
    
    with app.app_context():
        for project_data in projects_data:
            project = Project.query.get(project_data['id'])
            if project:
                # Convertir les heures en minutes
                initial_minutes = convert_hours_to_minutes(project_data['initial'])
                remaining_minutes = convert_hours_to_minutes(project_data['remaining'])
                
                # Afficher les valeurs avant modification
                print(f"\nProjet {project.id} - {project.name}:")
                print(f"Avant: initial={project.initial_credit}, remaining={project.remaining_credit}")
                
                # Mettre à jour les valeurs
                project.initial_credit = initial_minutes
                project.remaining_credit = remaining_minutes
                
                # Afficher les nouvelles valeurs
                print(f"Après: initial={initial_minutes}min ({initial_minutes/60:.2f}h), "
                      f"remaining={remaining_minutes}min ({remaining_minutes/60:.2f}h)")
            else:
                print(f"\nProjet {project_data['id']} non trouvé!")
        
        # Sauvegarder les modifications
        try:
            db.session.commit()
            print("\nModifications sauvegardées avec succès!")
        except Exception as e:
            db.session.rollback()
            print(f"\nErreur lors de la sauvegarde: {str(e)}")

if __name__ == '__main__':
    main()