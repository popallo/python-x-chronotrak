"""
Tests unitaires pour le modèle User.
"""

from app import db
from app.models.user import User


def test_user_creation(app, admin_user):
    """Test la création d'un utilisateur."""
    with app.app_context():
        # S'assurer que l'utilisateur est attaché à la session
        user = db.session.merge(admin_user)
        assert user.id is not None
        assert user.name == "Admin Test"
        assert user.email == "admin@test.com"
        assert user.role == "admin"


def test_user_password_hashing(app):
    """Test que les mots de passe sont correctement hashés."""
    user = User(name="Test User", email="test@example.com", role="technicien")
    password = "securepassword123"
    user.set_password(password)

    assert user.password_hash != password
    assert user.password_hash is not None
    assert len(user.password_hash) > 0


def test_user_check_password(app):
    """Test la vérification de mot de passe."""
    user = User(name="Test User", email="test@example.com", role="technicien")
    password = "securepassword123"
    user.set_password(password)

    assert user.check_password(password) is True
    assert user.check_password("wrongpassword") is False


def test_user_is_admin(app):
    """Test la méthode is_admin()."""
    admin = User(name="Admin", email="admin@test.com", role="admin")
    tech = User(name="Tech", email="tech@test.com", role="technicien")
    client = User(name="Client", email="client@test.com", role="client")

    assert admin.is_admin() is True
    assert tech.is_admin() is False
    assert client.is_admin() is False


def test_user_is_client(app):
    """Test la méthode is_client()."""
    admin = User(name="Admin", email="admin@test.com", role="admin")
    tech = User(name="Tech", email="tech@test.com", role="technicien")
    client = User(name="Client", email="client@test.com", role="client")

    assert client.is_client() is True
    assert admin.is_client() is False
    assert tech.is_client() is False


def test_user_is_technician(app):
    """Test la méthode is_technician()."""
    admin = User(name="Admin", email="admin@test.com", role="admin")
    tech = User(name="Tech", email="tech@test.com", role="technicien")
    client = User(name="Client", email="client@test.com", role="client")

    assert tech.is_technician() is True
    assert admin.is_technician() is False
    assert client.is_technician() is False


def test_user_has_access_to_client(app, admin_user, technician_user, client_user, test_client):
    """Test la méthode has_access_to_client()."""
    with app.app_context():
        # S'assurer que tous les objets sont attachés à la session
        admin = db.session.merge(admin_user)
        tech = db.session.merge(technician_user)
        client_user_obj = db.session.merge(client_user)
        client = db.session.merge(test_client)

        # Admin et technicien ont accès à tous les clients
        assert admin.has_access_to_client(client.id) is True
        assert tech.has_access_to_client(client.id) is True

        # Client sans association n'a pas accès
        assert client_user_obj.has_access_to_client(client.id) is False

        # Associer le client à l'utilisateur client
        client_user_obj.clients.append(client)
        db.session.commit()
        db.session.refresh(client_user_obj)

        # Maintenant l'utilisateur client a accès
        assert client_user_obj.has_access_to_client(client.id) is True


def test_user_repr(app):
    """Test la représentation string d'un utilisateur."""
    user = User(name="Test User", email="test@example.com", role="technicien")
    repr_str = repr(user)
    assert "Test User" in repr_str
    assert "test@example.com" in repr_str
    assert "technicien" in repr_str
