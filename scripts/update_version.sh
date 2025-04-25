#!/bin/bash
# Script pour mettre à jour automatiquement la version de l'application ChronoTrak
# Utilisation: ./scripts/update_version.sh [major|minor|patch]

set -e

# Chemin du fichier VERSION
VERSION_FILE="app/VERSION"

# Vérifier si le fichier VERSION existe
if [ ! -f "$VERSION_FILE" ]; then
    echo "Le fichier VERSION n'existe pas. Création avec la version 1.0.0"
    echo "1.0.0" > "$VERSION_FILE"
fi

# Lire la version actuelle
CURRENT_VERSION=$(cat "$VERSION_FILE")
echo "Version actuelle: $CURRENT_VERSION"

# Découper la version en composants
IFS='.' read -r -a VERSION_PARTS <<< "$CURRENT_VERSION"
MAJOR="${VERSION_PARTS[0]}"
MINOR="${VERSION_PARTS[1]}"
PATCH="${VERSION_PARTS[2]}"

# Déterminer quel composant de version doit être incrémenté
INCREMENT_TYPE="${1:-patch}"  # Par défaut, on incrémente le patch

case "$INCREMENT_TYPE" in
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    patch)
        PATCH=$((PATCH + 1))
        ;;
    *)
        echo "Type d'incrémentation non reconnu: $INCREMENT_TYPE. Utilisation de 'patch'."
        PATCH=$((PATCH + 1))
        ;;
esac

# Construire la nouvelle version
NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
echo "Nouvelle version: $NEW_VERSION"

# Mettre à jour le fichier VERSION
echo "$NEW_VERSION" > "$VERSION_FILE"

# Commit si git est disponible et si nous sommes dans un repo git
if command -v git &> /dev/null && git rev-parse --is-inside-work-tree &> /dev/null; then
    git add "$VERSION_FILE"
    git commit -m "build: bump version to $NEW_VERSION"
    
    # Créer un tag si demandé
    if [ "${2:-}" = "--tag" ]; then
        git tag -a "v$NEW_VERSION" -m "Version $NEW_VERSION"
        echo "Tag v$NEW_VERSION créé"
    fi
    
    echo "Changement de version commité"
else
    echo "Git n'est pas disponible ou nous ne sommes pas dans un repo git. Pas de commit automatique."
fi

echo "Version mise à jour avec succès."