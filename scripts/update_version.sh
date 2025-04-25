#!/bin/bash
# Script pour mettre à jour automatiquement la version de l'application ChronoTrak
# basé sur les branches GitFlow

set -e

# Chemin du fichier VERSION
VERSION_FILE="app/VERSION"

# Vérifier si le fichier VERSION existe
if [ ! -f "$VERSION_FILE" ]; then
    echo "Le fichier VERSION n'existe pas. Création avec la version v1.0.0"
    echo -n "v1.0.0" > "$VERSION_FILE"
fi

# Lire la version actuelle
CURRENT_VERSION=$(cat "$VERSION_FILE")
echo "Version actuelle dans $VERSION_FILE: $CURRENT_VERSION"

# Détecter la version depuis la branche GitFlow
branch_name=$(git branch --show-current)
echo "Branche actuelle: $branch_name"

# Essayons directement avec un pattern match simple pour extraire la version avec le 'v'
GITFLOW_VERSION=""

# Cas 1: La branche est directement "v1.2.3"
if [[ $branch_name =~ ^(v[0-9]+\.[0-9]+\.[0-9]+)$ ]]; then
    GITFLOW_VERSION="${BASH_REMATCH[1]}"
    echo "Version extraite du nom de branche: $GITFLOW_VERSION"
# Cas 2: La branche est "release/v1.2.3"
elif [[ $branch_name =~ release/(v[0-9]+\.[0-9]+\.[0-9]+)$ ]]; then
    GITFLOW_VERSION="${BASH_REMATCH[1]}"
    echo "Version extraite du nom de branche: $GITFLOW_VERSION"
fi

# Si on a trouvé une version dans le nom de la branche
if [ -n "$GITFLOW_VERSION" ]; then
    echo "Version détectée: $GITFLOW_VERSION"
    
    # Seulement si la version est différente, mettre à jour
    if [ "$GITFLOW_VERSION" != "$CURRENT_VERSION" ]; then
        echo "Mise à jour du fichier VERSION avec: $GITFLOW_VERSION"
        echo -n "$GITFLOW_VERSION" > "$VERSION_FILE"
        
        # Commit si git est disponible 
        if [ -z "$NO_COMMIT" ] && command -v git &> /dev/null && git rev-parse --is-inside-work-tree &> /dev/null; then
            git add "$VERSION_FILE"
            git commit -m "build: bump version to $GITFLOW_VERSION"
            echo "Changement de version commité"
        else
            echo "Pas de commit automatique."
        fi
        
        echo "Version mise à jour avec succès."
    else
        echo "Version déjà à jour, aucune modification nécessaire."
    fi
else
    echo "Aucune version détectée dans le nom de la branche '$branch_name'."
    
    # Option pour incrémenter manuellement
    if [ "$1" == "major" ] || [ "$1" == "minor" ] || [ "$1" == "patch" ]; then
        INCREMENT_TYPE="$1"
        
        # Découper la version actuelle (en retirant le v si présent)
        VERSION_NUMBER=${CURRENT_VERSION#v}
        IFS='.' read -r -a VERSION_PARTS <<< "$VERSION_NUMBER"
        MAJOR="${VERSION_PARTS[0]}"
        MINOR="${VERSION_PARTS[1]}"
        PATCH="${VERSION_PARTS[2]}"
        
        # Incrémenter selon le type
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
        esac
        
        # Construire la nouvelle version (en conservant le v si présent dans la version actuelle)
        if [[ "$CURRENT_VERSION" == v* ]]; then
            NEW_VERSION="v${MAJOR}.${MINOR}.${PATCH}"
        else
            NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
        fi
        
        echo "Nouvelle version (après incrémentation $INCREMENT_TYPE): $NEW_VERSION"
        
        # Mettre à jour le fichier
        echo -n "$NEW_VERSION" > "$VERSION_FILE"
        
        # Commit si demandé
        if [ -z "$NO_COMMIT" ] && command -v git &> /dev/null && git rev-parse --is-inside-work-tree &> /dev/null; then
            git add "$VERSION_FILE"
            git commit -m "build: bump version to $NEW_VERSION ($INCREMENT_TYPE)"
            echo "Changement de version commité"
        fi
        
        echo "Version mise à jour avec succès."
    elif [ "$1" == "--set" ] && [ -n "$2" ]; then
        # Définir une version spécifique
        NEW_VERSION="$2"
        # Ajouter 'v' si pas présent et si la version actuelle l'a
        if [[ "$CURRENT_VERSION" == v* ]] && [[ "$NEW_VERSION" != v* ]]; then
            NEW_VERSION="v$NEW_VERSION"
        fi
        
        echo "Définition manuelle de la version: $NEW_VERSION"
        
        # Mettre à jour le fichier
        echo -n "$NEW_VERSION" > "$VERSION_FILE"
        
        # Commit si demandé
        if [ -z "$NO_COMMIT" ] && command -v git &> /dev/null && git rev-parse --is-inside-work-tree &> /dev/null; then
            git add "$VERSION_FILE"
            git commit -m "build: définition de la version à $NEW_VERSION"
            echo "Changement de version commité"
        fi
        
        echo "Version mise à jour avec succès."
    else
        echo "Aucune action effectuée sur la version."
    fi
fi