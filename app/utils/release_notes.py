"""
Notes de version (release notes) pour l'application ChronoTrak.
Source de vérité : RELEASE_NOTES.yaml à la racine du projet.
À mettre à jour à chaque release (manuellement ou via scripts/release_note_add.py).
"""

import os

# Racine du projet (parent du package app : app/utils -> app -> racine)
_APP_ROOT = os.path.dirname(os.path.dirname(__file__))
_PROJECT_ROOT = os.path.dirname(_APP_ROOT)
_RELEASE_NOTES_FILE = os.path.join(_PROJECT_ROOT, "RELEASE_NOTES.yaml")


def _load_from_yaml():
    """Charge les release notes depuis RELEASE_NOTES.yaml. Retourne None si indisponible."""
    try:
        import yaml
    except ImportError:
        return None
    path = _RELEASE_NOTES_FILE
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, list):
            return data
        return None
    except Exception:
        return None


def get_release_notes():
    """
    Retourne la liste des release notes (la plus récente en premier).
    Charge depuis RELEASE_NOTES.yaml ; retourne une liste vide si fichier absent ou invalide.
    """
    notes = _load_from_yaml()
    if notes is None:
        return []
    # S'assurer que chaque entrée a la structure attendue (version, date, items)
    result = []
    for entry in notes:
        if not isinstance(entry, dict):
            continue
        version = entry.get("version")
        if not version:
            continue
        items = entry.get("items")
        if not isinstance(items, list):
            items = []
        result.append(
            {
                "version": str(version).strip(),
                "date": entry.get("date") or "",
                "items": [
                    {"type": (x.get("type") or "improvement").strip(), "text": (x.get("text") or "").strip()}
                    for x in items
                    if isinstance(x, dict) and x.get("text")
                ],
            }
        )
    return result
