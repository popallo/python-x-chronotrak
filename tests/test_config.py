"""
Tests de configuration de l'application Flask.
"""

from app import create_app


def test_testing_config():
    """Test que la configuration de test fonctionne correctement."""
    app = create_app("testing")
    assert app.config["TESTING"] is True
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///test.db"
    assert app.config["WTF_CSRF_ENABLED"] is True  # Par défaut activé


def test_development_config():
    """Test que la configuration de développement fonctionne."""
    app = create_app("development")
    assert app.config["DEBUG"] is True
    assert app.config["TESTING"] is False


def test_production_config():
    """Test que la configuration de production fonctionne."""
    app = create_app("production")
    assert app.config["DEBUG"] is False
    assert app.config["TESTING"] is False


def test_app_creation(app):
    """Test que l'application Flask se crée correctement."""
    assert app is not None
    assert app.config["TESTING"] is True


def test_database_initialization(app):
    """Test que la base de données s'initialise correctement."""
    from app import db

    with app.app_context():
        # Vérifier que les tables existent
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        assert "user" in tables
        assert "client" in tables
        assert "project" in tables
