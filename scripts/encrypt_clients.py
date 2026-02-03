"""
Script pour chiffrer les données existantes dans la base de données
À exécuter après avoir mis à jour les modèles et fait une migration Alembic
"""

import base64
import os

from app import create_app, db
from app.models.client import Client
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

# Vérifier la présence de la clé de chiffrement
encryption_key = os.environ.get("ENCRYPTION_KEY")
if not encryption_key:
    print("ATTENTION: Aucune clé de chiffrement n'est définie dans les variables d'environnement.")
    print("Voulez-vous générer une nouvelle clé? Cette clé devra être conservée pour toujours accéder aux données.")
    response = input("Générer une nouvelle clé? (y/n): ")

    if response.lower() == "y":
        encryption_key = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8")
        print(f"\nNouvelle clé générée: {encryption_key}")
        print("IMPORTANT: Sauvegardez cette clé dans un endroit sûr!")
        print("Définissez-la comme variable d'environnement ENCRYPTION_KEY dans votre fichier .env")

        # Écrire la clé dans un fichier temporaire
        with open("encryption_key_temp.txt", "w") as f:
            f.write(f"ENCRYPTION_KEY={encryption_key}")

        print("La clé a également été écrite dans le fichier 'encryption_key_temp.txt'")
        print("Copiez cette valeur dans votre fichier .env et supprimez ensuite ce fichier temporaire")
    else:
        print("Opération annulée. Une clé de chiffrement est nécessaire pour continuer.")
        exit(1)

# Créer l'application avec le contexte
app = create_app("development")

with app.app_context():
    # Vérifier si la migration a déjà été effectuée
    print("Vérification des données existantes...")

    # Fonction pour vérifier si une chaîne est déjà chiffrée
    # (heuristique basique: les données chiffrées par Fernet commencent par 'gAAA')
    def is_encrypted(value):
        if not value:
            return True  # Les valeurs None ou vides sont considérées comme déjà traitées
        return isinstance(value, str) and value.startswith("gAAA")

    # Initialiser Fernet avec la clé
    fernet = Fernet(encryption_key.encode("utf-8"))

    # Récupérer tous les clients
    clients = Client.query.all()
    print(f"Trouvé {len(clients)} clients à traiter.")

    # Compteurs pour suivre la progression
    encrypted_count = 0
    already_encrypted_count = 0

    # Parcourir chaque client et chiffrer les données sensibles
    for client in clients:
        client_modified = False

        # Chiffrer email
        if client.email and not is_encrypted(client.email):
            client.email = fernet.encrypt(client.email.encode("utf-8")).decode("utf-8")
            client_modified = True
        elif client.email:
            already_encrypted_count += 1

        # Chiffrer phone
        if client.phone and not is_encrypted(client.phone):
            client.phone = fernet.encrypt(client.phone.encode("utf-8")).decode("utf-8")
            client_modified = True
        elif client.phone:
            already_encrypted_count += 1

        # Chiffrer address
        if client.address and not is_encrypted(client.address):
            client.address = fernet.encrypt(client.address.encode("utf-8")).decode("utf-8")
            client_modified = True
        elif client.address:
            already_encrypted_count += 1

        # Chiffrer notes
        if client.notes and not is_encrypted(client.notes):
            client.notes = fernet.encrypt(client.notes.encode("utf-8")).decode("utf-8")
            client_modified = True
        elif client.notes:
            already_encrypted_count += 1

        if client_modified:
            encrypted_count += 1

    # Enregistrer les modifications
    if encrypted_count > 0:
        print(f"Chiffrement de {encrypted_count} clients...")
        db.session.commit()
        print("Chiffrement terminé avec succès!")
    else:
        print("Aucune donnée à chiffrer. Les données sont peut-être déjà chiffrées ou absentes.")

    if already_encrypted_count > 0:
        print(f"{already_encrypted_count} champs étaient déjà chiffrés et ont été ignorés.")

    print("\nRappel important:")
    print("1. Assurez-vous que la clé de chiffrement est sauvegardée en lieu sûr")
    print("2. Définissez ENCRYPTION_KEY dans votre fichier .env pour la production")
    print("3. Effectuez une sauvegarde de votre base de données après cette opération")
