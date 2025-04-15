## Cloner le projet

```bash
git clone <url-du-repo> chronotrak
cd chronotrak
```

## Créer un environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # Sur Linux/Mac
```

ou

```bash
venv\Scripts\activate  # Sur Windows
```

## Installer les dépendances

```bash
pip install -r requirements.txt
```

## Configurer la base de données

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## Lancer l'application

```bash
flask run
```

## Ajouter le compte utilisateur super admin

```bash
python3 create_admin.py
```