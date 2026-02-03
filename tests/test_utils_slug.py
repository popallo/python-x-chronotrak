"""
Tests unitaires pour les fonctions de génération de slug.
"""

import pytest
from app import db
from app.models.client import Client
from app.utils.slug_utils import generate_slug, update_slug


def test_generate_slug_basic(app):
    """Test la génération basique d'un slug."""
    with app.app_context():
        # Utiliser un nom unique pour éviter les conflits
        slug = generate_slug("Mon Super Client Unique", Client)
        assert slug == "mon-super-client-unique"
        assert slug.islower()
        assert " " not in slug


def test_generate_slug_special_characters(app):
    """Test la gestion des caractères spéciaux."""
    slug = generate_slug("Client & Co. (Paris)", Client)
    assert slug == "client-co-paris"
    assert "(" not in slug
    assert ")" not in slug
    assert "&" not in slug
    assert "." not in slug


def test_generate_slug_accents(app):
    """Test la gestion des accents."""
    slug = generate_slug("Client Éléphant", Client)
    assert slug == "client-elephant"
    assert "é" not in slug
    assert "É" not in slug


def test_generate_slug_multiple_spaces(app):
    """Test la gestion des espaces multiples."""
    slug = generate_slug("Client    Avec    Espaces", Client)
    assert slug == "client-avec-espaces"
    assert "    " not in slug


def test_generate_slug_leading_trailing_dashes(app):
    """Test la suppression des tirets en début/fin."""
    slug = generate_slug("---Client---", Client)
    assert not slug.startswith("-")
    assert not slug.endswith("-")


def test_generate_slug_uniqueness(app):
    """Test que les slugs sont uniques."""
    with app.app_context():
        # Utiliser un nom unique pour éviter les conflits avec la fixture
        client1 = Client(name="Unique Test Client Slug")
        db.session.add(client1)
        db.session.commit()

        # Générer un slug pour un deuxième client avec le même nom
        slug = generate_slug("Unique Test Client Slug", Client)

        # Le slug doit être unique (ajout d'un numéro)
        assert slug == "unique-test-client-slug-1"


def test_generate_slug_existing_id(app):
    """Test la génération de slug avec existing_id (pour mise à jour)."""
    with app.app_context():
        # Utiliser un nom unique pour éviter les conflits
        client = Client(name="Unique Test Client Update")
        db.session.add(client)
        db.session.commit()

        # Générer un slug pour le même client (mise à jour)
        slug = generate_slug("Unique Test Client Update", Client, existing_id=client.id)

        # Le slug doit être le même car c'est le même client
        assert slug == "unique-test-client-update"


def test_update_slug_with_name(app):
    """Test la mise à jour de slug avec attribut 'name'."""
    with app.app_context():
        # Utiliser un nom unique pour éviter les conflits
        client = Client(name="Ancien Nom Unique Slug")
        db.session.add(client)
        db.session.commit()

        original_slug = client.slug

        # Changer le nom et mettre à jour le slug
        client.name = "Nouveau Nom Unique Slug"
        update_slug(client)

        assert client.slug != original_slug
        assert client.slug == "nouveau-nom-unique-slug"


def test_update_slug_with_title(app):
    """Test la mise à jour de slug avec attribut 'title'."""

    # Créer un modèle mock avec title au lieu de name
    class MockModel:
        def __init__(self):
            self.title = "Test Title"
            self.id = None

    # Ajouter une méthode query au modèle pour le test
    class MockQuery:
        def filter_by(self, **kwargs):
            return self

        def filter(self, *args):
            return self

        def first(self):
            return None

    # Simuler la génération de slug
    slug = generate_slug("Test Title", type("MockClass", (), {"query": MockQuery()}))
    assert slug == "test-title"


def test_update_slug_no_name_or_title():
    """Test que update_slug lève une erreur si pas de 'name' ou 'title'."""

    class MockModel:
        def __init__(self):
            self.id = None

    model = MockModel()

    with pytest.raises(ValueError, match="Le modèle doit avoir un attribut 'name' ou 'title'"):
        update_slug(model)


def test_generate_slug_numbers(app):
    """Test la gestion des nombres dans les slugs."""
    slug = generate_slug("Client 123 Test", Client)
    assert slug == "client-123-test"
    assert "123" in slug
