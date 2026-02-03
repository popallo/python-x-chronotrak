# Pre-commit : lint et format au commit

Les hooks pre-commit exécutent **Ruff** (lint + format) et quelques vérifications de base à chaque `git commit`. Le code est vérifié et peut être auto-corrigé avant d’être commité.

## Prérequis

- Git
- Environnement virtuel Python géré par **uv** (`.venv`)

## Installation (une seule fois)

À la racine du projet, avec ton environnement virtuel activé ou via `uv run` :

```bash
# 1. Activer le venv (optionnel si tu utilises "uv run" ensuite)
source .venv/bin/activate   # Linux/macOS
# ou sous Fish : source .venv/bin/activate.fish

# 2. Installer les dépendances de dev (pre-commit, ruff, etc.)
uv sync --extra dev

# 3. Installer le hook Git (à faire une fois par clone)
pre-commit install

# 4. (Recommandé) Lancer une fois sur tout le dépôt pour tout formater/linter
pre-commit run --all-files
```

Résultat : à chaque `git commit`, pre-commit lancera Ruff (lint + format) et les autres hooks sur les fichiers stagés.

## Commandes utiles

| Commande | Description |
|----------|-------------|
| `pre-commit run` | Lancer tous les hooks sur les fichiers stagés |
| `pre-commit run --all-files` | Lancer sur tout le dépôt (utile après installation) |
| `pre-commit run ruff --all-files` | Lancer uniquement Ruff sur tout le projet |
| `pre-commit run ruff-format --all-files` | Uniquement le formatage Ruff |
| `pre-commit autoupdate` | Mettre à jour les rev des hooks (versions) |

## Premier lancement sur tout le code

Après `pre-commit install`, tu peux formater et lint tout le dépôt une fois :

```bash
uv run pre-commit run --all-files
```

Si des corrections sont faites, les fichiers sont modifiés : vérifie les diffs puis re-stage et recommit si besoin.

## Commits en deux temps (Ruff + corrections)

Si Ruff a modifié beaucoup de fichiers et que tu veux séparer l’ajout de Ruff des corrections de code :

```bash
# Tout dé-stager
git reset

# 1) Commit « config Ruff + pre-commit » uniquement
git add .pre-commit-config.yaml pyproject.toml docs/PRE_COMMIT.md
# Si le lockfile a changé (nouvelles deps dev) :
git add uv.lock
git status   # vérifier : seulement config + doc
git commit -m "chore: add pre-commit and Ruff (config and dev deps)"

# 2) Commit « corrections appliquées par Ruff » (uniquement les fichiers Python)
git add config.py run.py wsgi.py
find app management tests migrations scripts -name "*.py" -print0 | xargs -0 git add
git status   # vérifier : seulement fichiers Python
git commit -m "style: apply Ruff formatting and lint fixes"
```

Les autres fichiers modifiés (templates, static, docker, etc.) restent en working tree pour des commits séparés si besoin.

## Contourner le hook (exceptionnel)

Pour un commit sans exécuter les hooks (à éviter en routine) :

```bash
git commit --no-verify -m "message"
```

## Configuration

- **Hooks** : `.pre-commit-config.yaml` (Ruff + pre-commit-hooks).
- **Ruff** : `pyproject.toml` sections `[tool.ruff]` et `[tool.ruff.format]`.

Les mêmes réglages Ruff sont utilisés en local (pre-commit) et dans le pipeline CI.
