"""
Configuration pytest avec fixtures communes pour tous les tests.
"""

import os
import tempfile

import pytest
from app import create_app, db
from app.models.client import Client
from app.models.project import Project
from app.models.user import User
from cryptography.fernet import Fernet
from sqlalchemy import text


@pytest.fixture(scope="function")
def app():
    """Crée une application Flask de test avec base de données temporaire."""
    # Générer une clé de chiffrement pour les tests
    test_encryption_key = Fernet.generate_key().decode()

    # Créer un fichier temporaire pour la base de données
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    # Configuration de test
    os.environ["ENCRYPTION_KEY"] = test_encryption_key
    os.environ["FLASK_ENV"] = "testing"

    app = create_app("testing")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False  # Désactiver CSRF pour les tests
    app.config["SECRET_KEY"] = "test-secret-key"

    with app.app_context():
        db.create_all()
        yield app
        # Nettoyer proprement avant de supprimer les tables
        db.session.remove()
        # Désactiver les contraintes FK pour SQLite avant de supprimer
        try:
            with db.engine.connect() as conn:
                conn.execute(text("PRAGMA foreign_keys=OFF"))
                conn.commit()
            db.drop_all()
        except Exception:
            # Si drop_all échoue, ignorer (le fichier sera supprimé de toute façon)
            pass
        finally:
            try:
                with db.engine.connect() as conn:
                    conn.execute(text("PRAGMA foreign_keys=ON"))
                    conn.commit()
            except Exception:
                pass

    # Nettoyer le fichier temporaire
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope="function")
def client(app):
    """Client de test Flask."""
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    """Runner CLI pour les tests."""
    return app.test_cli_runner()


@pytest.fixture(scope="function")
def admin_user(app):
    """Crée un utilisateur administrateur de test."""
    with app.app_context():
        user = User(name="Admin Test", email="admin@test.com", role="admin")
        user.set_password("testpassword")
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)  # Rafraîchir pour éviter DetachedInstanceError
        return user


@pytest.fixture(scope="function")
def technician_user(app):
    """Crée un utilisateur technicien de test."""
    with app.app_context():
        user = User(name="Technicien Test", email="tech@test.com", role="technicien")
        user.set_password("testpassword")
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)  # Rafraîchir pour éviter DetachedInstanceError
        return user


@pytest.fixture(scope="function")
def client_user(app):
    """Crée un utilisateur client de test."""
    with app.app_context():
        user = User(name="Client Test", email="client@test.com", role="client")
        user.set_password("testpassword")
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)  # Rafraîchir pour éviter DetachedInstanceError
        return user


@pytest.fixture(scope="function")
def test_client(app):
    """Crée un client de test."""
    with app.app_context():
        client = Client(name="Client Test", email="client@example.com", phone="0123456789")
        db.session.add(client)
        db.session.commit()
        db.session.refresh(client)  # Rafraîchir pour éviter DetachedInstanceError
        return client


@pytest.fixture(scope="function")
def test_project(app, test_client):
    """Crée un projet de test."""
    with app.app_context():
        # S'assurer que test_client est attaché à la session
        if test_client.id:
            test_client = db.session.merge(test_client)

        project = Project(
            name="Projet Test",
            client_id=test_client.id,
            initial_credit=600,  # 10 heures en minutes
            remaining_credit=600,
            time_tracking_enabled=True,
        )
        db.session.add(project)
        db.session.commit()
        db.session.refresh(project)  # Rafraîchir pour éviter DetachedInstanceError
        return project
