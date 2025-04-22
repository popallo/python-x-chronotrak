"""
Script pour chiffrer les commentaires existants dans la base de données
À exécuter après avoir mis à jour les modèles et fait une migration Alembic
"""
from app import create_app, db
from app.models.task import Comment
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()

# Vérifier la présence de la clé de chiffrement
encryption_key = os.environ.get('ENCRYPTION_KEY')
if not encryption_key:
    print("ERREUR: Aucune clé de chiffrement n'est définie dans les variables d'environnement.")
    print("Définissez ENCRYPTION_KEY dans votre fichier .env avant de continuer.")
    exit(1)

# Créer l'application avec le contexte
app = create_app('development')

def is_encrypted(value):
    """Vérifie si une valeur semble déjà être chiffrée"""
    if not value:
        return True  # Les valeurs None ou vides sont considérées comme déjà traitées
    return isinstance(value, str) and value.startswith('gAAA')

with app.app_context():
    # Initialiser Fernet avec la clé
    fernet = Fernet(encryption_key.encode('utf-8'))
    
    # Récupérer tous les commentaires
    comments = Comment.query.all()
    print(f"Trouvé {len(comments)} commentaires à traiter.")
    
    # Compteurs pour suivre la progression
    encrypted_count = 0
    already_encrypted_count = 0
    error_count = 0
    
    # Parcourir chaque commentaire et chiffrer le contenu
    for comment in comments:
        try:
            if comment.content and not is_encrypted(comment.content):
                original_content = comment.content
                # Chiffrer le contenu
                encrypted_content = fernet.encrypt(original_content.encode('utf-8')).decode('utf-8')
                comment.content = encrypted_content
                encrypted_count += 1
            elif comment.content and is_encrypted(comment.content):
                already_encrypted_count += 1
        except Exception as e:
            print(f"Erreur lors du chiffrement du commentaire {comment.id}: {e}")
            error_count += 1
    
    # Enregistrer les modifications
    if encrypted_count > 0:
        print(f"Chiffrement de {encrypted_count} commentaires...")
        db.session.commit()
        print("Chiffrement terminé avec succès!")
    else:
        print("Aucun commentaire à chiffrer. Les commentaires sont peut-être déjà chiffrés ou absents.")
    
    if already_encrypted_count > 0:
        print(f"{already_encrypted_count} commentaires étaient déjà chiffrés et ont été ignorés.")
    
    if error_count > 0:
        print(f"ATTENTION: {error_count} erreurs ont été rencontrées. Certains commentaires n'ont pas pu être chiffrés.")
        
    print("\nRappel important:")
    print("1. Assurez-vous que la clé de chiffrement est sauvegardée en lieu sûr")
    print("2. Effectuez une sauvegarde de votre base de données après cette opération")