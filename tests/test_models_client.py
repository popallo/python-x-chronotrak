"""
Tests unitaires pour le modèle Client.
"""

from app import db
from app.models.client import Client
from sqlalchemy import text


def test_client_creation(app, test_client):
    """Test la création d'un client."""
    with app.app_context():
        # S'assurer que le client est attaché à la session
        client = db.session.merge(test_client)
        assert client.id is not None
        assert client.name == "Client Test"
        assert client.slug is not None
        assert len(client.slug) > 0


def test_client_slug_generation(app):
    """Test la génération automatique de slug."""
    with app.app_context():
        # Utiliser un nom unique pour éviter les conflits avec d'autres tests
        client = Client(name="Mon Super Client Unique")
        db.session.add(client)
        db.session.commit()

        assert client.slug == "mon-super-client-unique"
        assert client.slug is not None


def test_client_slug_uniqueness(app):
    """Test que les slugs sont uniques."""
    with app.app_context():
        # Utiliser un nom unique pour éviter les conflits avec la fixture test_client
        client1 = Client(name="Unique Test Client")
        db.session.add(client1)
        db.session.commit()

        client2 = Client(name="Unique Test Client")
        db.session.add(client2)
        db.session.commit()

        assert client1.slug == "unique-test-client"
        assert client2.slug == "unique-test-client-1"  # Doit être unique


def test_client_encrypted_email(app):
    """Test le chiffrement/déchiffrement de l'email."""
    with app.app_context():
        email = "test@example.com"
        client = Client(name="Test Client", email=email)
        db.session.add(client)
        db.session.commit()

        # Recharger depuis la base pour voir la valeur chiffrée
        client_id = client.id
        db.session.expunge(client)
        client_from_db = db.session.get(Client, client_id)

        # L'email via la propriété doit être déchiffré correctement
        assert client_from_db.email == email

        # Vérifier que la valeur brute dans la base est chiffrée
        # En accédant directement à la colonne via une requête SQL brute
        result = db.session.execute(text("SELECT email FROM client WHERE id = :id"), {"id": client_id}).fetchone()

        if result and result[0]:
            raw_email = result[0]
            # La valeur brute doit être chiffrée (commence par 'gAAA' pour Fernet)
            assert raw_email != email
            assert raw_email.startswith("gAAA")  # Format Fernet


def test_client_encrypted_phone(app):
    """Test le chiffrement/déchiffrement du téléphone."""
    with app.app_context():
        phone = "0123456789"
        client = Client(name="Test Client", phone=phone)
        db.session.add(client)
        db.session.commit()

        # Recharger depuis la base pour voir la valeur chiffrée
        client_id = client.id
        db.session.expunge(client)
        client_from_db = db.session.get(Client, client_id)

        # Le téléphone via la propriété doit être déchiffré correctement
        assert client_from_db.phone == phone

        # Vérifier que la valeur brute dans la base est chiffrée
        result = db.session.execute(text("SELECT phone FROM client WHERE id = :id"), {"id": client_id}).fetchone()

        if result and result[0]:
            raw_phone = result[0]
            # La valeur brute doit être chiffrée
            assert raw_phone != phone
            assert raw_phone.startswith("gAAA")  # Format Fernet


def test_client_encrypted_address(app):
    """Test le chiffrement/déchiffrement de l'adresse."""
    address = "123 Rue de Test, 75000 Paris"
    client = Client(name="Test Client", address=address)
    db.session.add(client)
    db.session.commit()

    assert client.address == address


def test_client_encrypted_notes(app):
    """Test le chiffrement/déchiffrement des notes."""
    notes = "Notes importantes sur le client"
    client = Client(name="Test Client", notes=notes)
    db.session.add(client)
    db.session.commit()

    assert client.notes == notes


def test_client_slug_update_on_name_change(app):
    """Test que le slug se met à jour si le nom change."""
    with app.app_context():
        client = Client(name="Ancien Nom Unique")
        db.session.add(client)
        db.session.commit()

        original_slug = client.slug

        client.name = "Nouveau Nom Unique"
        client.save()

        assert client.slug != original_slug
        assert client.slug == "nouveau-nom-unique"


def test_client_repr(app):
    """Test la représentation string d'un client."""
    client = Client(name="Test Client", email="test@example.com")
    repr_str = repr(client)
    assert "Test Client" in repr_str
    assert "test@example.com" in repr_str
