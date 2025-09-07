#!/usr/bin/env python3
"""
Script pour chiffrer les données non chiffrées existantes
Ce script résout le problème des warnings "Valeur non chiffrée détectée"
"""
import os
import sys
from dotenv import load_dotenv

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def is_encrypted(value):
    """Vérifie si une valeur semble déjà être chiffrée"""
    if not value:
        return True  # Les valeurs None ou vides sont considérées comme déjà traitées
    return isinstance(value, str) and value.startswith('gAAA')

def main():
    # Vérifier la présence de la clé de chiffrement
    encryption_key = os.environ.get('ENCRYPTION_KEY')
    if not encryption_key:
        print("ERREUR: Aucune clé de chiffrement n'est définie dans les variables d'environnement.")
        print("Définissez ENCRYPTION_KEY dans votre fichier .env avant de continuer.")
        return 1

    try:
        from app import create_app, db
        from app.models.client import Client
        from app.models.task import Comment
        from app.models.communication import Communication
        from cryptography.fernet import Fernet
        
        # Créer l'application avec le contexte
        app = create_app('development')
        
        with app.app_context():
            # Initialiser Fernet avec la clé
            fernet = Fernet(encryption_key.encode('utf-8'))
            
            total_encrypted = 0
            
            # 1. Chiffrer les données des clients
            print("Vérification des clients...")
            clients = Client.query.all()
            client_encrypted = 0
            
            for client in clients:
                fields_to_encrypt = ['email', 'phone', 'address', 'notes']
                for field in fields_to_encrypt:
                    value = getattr(client, field)
                    if value and not is_encrypted(value):
                        encrypted_value = fernet.encrypt(value.encode('utf-8')).decode('utf-8')
                        setattr(client, field, encrypted_value)
                        client_encrypted += 1
            
            if client_encrypted > 0:
                print(f"Chiffrement de {client_encrypted} champs clients...")
                total_encrypted += client_encrypted
            
            # 2. Chiffrer les commentaires
            print("Vérification des commentaires...")
            comments = Comment.query.all()
            comment_encrypted = 0
            
            for comment in comments:
                if comment.content and not is_encrypted(comment.content):
                    encrypted_content = fernet.encrypt(comment.content.encode('utf-8')).decode('utf-8')
                    comment.content = encrypted_content
                    comment_encrypted += 1
            
            if comment_encrypted > 0:
                print(f"Chiffrement de {comment_encrypted} commentaires...")
                total_encrypted += comment_encrypted
            
            # 3. Chiffrer les communications
            print("Vérification des communications...")
            communications = Communication.query.all()
            comm_encrypted = 0
            
            for comm in communications:
                fields_to_encrypt = ['content_html', 'content_text']
                for field in fields_to_encrypt:
                    value = getattr(comm, field)
                    if value and not is_encrypted(value):
                        encrypted_value = fernet.encrypt(value.encode('utf-8')).decode('utf-8')
                        setattr(comm, field, encrypted_value)
                        comm_encrypted += 1
            
            if comm_encrypted > 0:
                print(f"Chiffrement de {comm_encrypted} champs de communication...")
                total_encrypted += comm_encrypted
            
            # Sauvegarder les modifications
            if total_encrypted > 0:
                print(f"\nSauvegarde de {total_encrypted} modifications...")
                db.session.commit()
                print("✅ Chiffrement terminé avec succès!")
                print("Les warnings 'Valeur non chiffrée détectée' devraient maintenant disparaître.")
            else:
                print("✅ Aucune donnée non chiffrée trouvée. Toutes les données sont déjà chiffrées.")
            
            return 0
            
    except ImportError as e:
        print(f"ERREUR: Impossible d'importer les modules nécessaires: {e}")
        print("Assurez-vous d'être dans le bon répertoire et que l'environnement virtuel est activé.")
        return 1
    except Exception as e:
        print(f"ERREUR: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
