# Tests unitaires ChronoTrak

Ce répertoire contient les tests unitaires pour l'application ChronoTrak.

## Structure

```
tests/
├── __init__.py
├── conftest.py              # Configuration pytest (fixtures communes)
├── test_config.py           # Tests de configuration Flask
├── test_models_user.py      # Tests du modèle User
├── test_models_client.py    # Tests du modèle Client
├── test_models_project.py   # Tests du modèle Project
├── test_utils_time_format.py # Tests format_time
├── test_utils_slug.py       # Tests génération slug
└── test_utils_init.py       # Tests utilitaires de base
```

## Exécution des tests

### Avec uv (recommandé)

```bash
# Activer l'environnement virtuel
source .venv/bin/activate

# Exécuter tous les tests
uv run pytest

# Exécuter avec couverture de code
uv run pytest --cov=app --cov-report=term-missing

# Exécuter un fichier de test spécifique
uv run pytest tests/test_models_user.py

# Exécuter un test spécifique
uv run pytest tests/test_models_user.py::test_user_is_admin

# Mode verbose (affiche plus de détails)
uv run pytest -v

# Mode très verbose (affiche les print)
uv run pytest -vv -s

# Exécuter les tests en parallèle (plus rapide)
uv run pytest -n auto
```

### Avec pytest directement (si .venv est activé)

```bash
# Activer l'environnement virtuel
source .venv/bin/activate

# Exécuter tous les tests
pytest

# Avec couverture
pytest --cov=app --cov-report=term-missing --cov-report=html

# Ouvrir le rapport HTML de couverture
# (généré dans htmlcov/index.html)
```

## Configuration

Les tests utilisent :
- **Base de données** : SQLite en mémoire (`sqlite:///:memory:`) ou fichier temporaire
- **Configuration** : `TestingConfig` (définie dans `config.py`)
- **Fixtures** : Définies dans `conftest.py` (app, client, users, etc.)

## Variables d'environnement

Les tests génèrent automatiquement une clé de chiffrement pour les tests. Vous pouvez aussi définir :

```bash
export ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
export FLASK_ENV=testing
```

## Ajouter de nouveaux tests

1. Créer un nouveau fichier `test_*.py` dans `tests/`
2. Importer les fixtures nécessaires depuis `conftest.py`
3. Utiliser les décorateurs pytest (`@pytest.fixture`, `@pytest.mark.parametrize`, etc.)

Exemple :

```python
import pytest
from app.models.user import User

def test_my_new_feature(app):
    """Test ma nouvelle fonctionnalité."""
    with app.app_context():
        user = User(name='Test', email='test@example.com', role='admin')
        # ... votre test
        assert user.name == 'Test'
```

## Couverture de code

Pour générer un rapport de couverture HTML :

```bash
uv run pytest --cov=app --cov-report=html
```

Le rapport sera généré dans `htmlcov/index.html`. Ouvrez-le dans votre navigateur pour voir la couverture détaillée.

## Intégration CI/CD

Les tests sont exécutés automatiquement dans le pipeline CI/CD (`.gitea/workflows/cicd.yml`) :
- Tous les tests doivent passer
- La couverture de code est générée
- Le pipeline échoue si aucun test n'est trouvé
