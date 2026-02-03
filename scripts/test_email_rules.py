#!/usr/bin/env python3
"""
Script de test pour vérifier les nouvelles règles d'envoi d'emails
"""

import os
import sys

# Ajouter le répertoire parent au path pour pouvoir importer l'application
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.utils.email import send_email, send_task_notification


def test_email_rules():
    """Test des nouvelles règles d'envoi d'emails"""

    # Créer l'application
    app = create_app("development")

    with app.app_context():
        print("=== Test des règles d'envoi d'emails ===\n")

        # Récupérer les utilisateurs
        admins = User.query.filter_by(role="admin").all()
        clients = User.query.filter_by(role="client").all()

        print(f"Administrateurs trouvés: {len(admins)}")
        for admin in admins:
            print(f"  - {admin.name} ({admin.email})")

        print(f"\nClients trouvés: {len(clients)}")
        for client in clients:
            print(f"  - {client.name} ({client.email})")

        # Récupérer un projet pour les tests
        project = Project.query.first()
        if not project:
            print("\n❌ Aucun projet trouvé pour les tests")
            return

        print(f"\nProjet de test: {project.name} (Client: {project.client.name})")

        # Test 1: Email simple en dev
        print("\n--- Test 1: Email simple ---")
        subject = "Test email simple"
        text = "Ceci est un test d'email simple"
        html = "<h1>Test email simple</h1><p>Ceci est un test d'email simple</p>"

        # Simuler un environnement de développement
        app.config["FLASK_ENV"] = "development"

        print("Environnement: DEVELOPMENT")
        print("Destinataires initiaux: ['test@example.com']")

        success = send_email(subject, ["test@example.com"], text, html, email_type="test")
        print(f"Résultat: {'✅ Succès' if success else '❌ Échec'}")

        # Test 2: Email simple en production
        print("\n--- Test 2: Email simple en production ---")
        app.config["FLASK_ENV"] = "production"

        print("Environnement: PRODUCTION")
        print("Destinataires initiaux: ['test@example.com']")

        success = send_email(subject, ["test@example.com"], text, html, email_type="test")
        print(f"Résultat: {'✅ Succès' if success else '❌ Échec'}")

        # Test 3: Email lié à un projet en production
        print("\n--- Test 3: Email lié à un projet en production ---")
        print("Environnement: PRODUCTION")
        print(f"Projet: {project.name}")
        print("Destinataires initiaux: ['test@example.com']")

        success = send_email(
            subject, ["test@example.com"], text, html, email_type="task_status_change", project_id=project.id
        )
        print(f"Résultat: {'✅ Succès' if success else '❌ Échec'}")

        # Test 4: Notification de tâche
        print("\n--- Test 4: Notification de tâche ---")
        task = Task.query.filter_by(project_id=project.id).first()
        if task:
            print(f"Tâche: {task.title}")
            print("Environnement: PRODUCTION")

            success = send_task_notification(
                task=task,
                event_type="status_change",
                user=admins[0] if admins else None,
                additional_data={"old_status": "en cours", "new_status": "terminé"},
                notify_all=True,
            )
            print(f"Résultat: {'✅ Succès' if success else '❌ Échec'}")
        else:
            print("❌ Aucune tâche trouvée pour le test")

        # Test 5: Email uniquement aux administrateurs
        print("\n--- Test 5: Email uniquement aux administrateurs ---")
        admin_emails = [admin.email for admin in admins if admin.email]
        if admin_emails:
            print("Environnement: PRODUCTION")
            print(f"Destinataires initiaux: {admin_emails}")

            success = send_email(subject, admin_emails, text, html, email_type="admin_only")
            print(f"Résultat: {'✅ Succès' if success else '❌ Échec'}")
        else:
            print("❌ Aucun administrateur avec email trouvé")

        print("\n=== Fin des tests ===")


if __name__ == "__main__":
    test_email_rules()
