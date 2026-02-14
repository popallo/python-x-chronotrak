"""
Gestion sécurisée des pièces jointes des tâches.

- Stockage dans une arborescence dérivée (hash task_id + salt), non devinable.
- Fichiers stockés sous UUID (sans extension dans le nom) ; métadonnées dans manifest.json.
- Validation : whitelist d’extensions + vérification des magic bytes.
- Accès uniquement via les routes Flask (vérification d’accès à la tâche).
"""

import hashlib
import json
import re
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

from flask import current_app

# Extensions autorisées (lowercase)
ALLOWED_EXTENSIONS = frozenset({"csv", "pdf", "zip", "doc", "docx", "xls", "xlsx", "7z", "tar", "gz"})

# Magic bytes (début de fichier) pour validation
# Voir https://en.wikipedia.org/wiki/List_of_file_signatures
_MAGIC_SIGNATURES = {
    "pdf": (b"%PDF",),
    "zip": (b"PK\x03\x04", b"PK\x05\x06"),  # ZIP ou DOCX/XLSX (Office Open XML)
    "doc": (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",),  # OLE / MS Office legacy
    "docx": (b"PK\x03\x04",),  # Office Open XML
    "xls": (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",),
    "xlsx": (b"PK\x03\x04",),
    "7z": (b"7z\xbc\xaf\x27\x1c",),
    "tar": (b"",),  # TAR n'a pas de signature unique ; on valide par extension
    "gz": (b"\x1f\x8b",),
    "csv": None,  # Texte ; validé uniquement par extension + pas de binaire
}

MANIFEST_FILENAME = "manifest.json"


def _get_base_dir():
    path = current_app.config.get("TASK_ATTACHMENTS_UPLOAD_FOLDER")
    if not path:
        raise RuntimeError("TASK_ATTACHMENTS_UPLOAD_FOLDER is not configured")
    return Path(path)


def _task_dir_hash(task_id: int) -> str:
    """Dérive un nom de répertoire non devinable à partir de task_id."""
    salt = current_app.config.get("TASK_ATTACHMENTS_PATH_SALT", "chronotrak_task_attachments_v1")
    data = f"{task_id}:{salt}:task_attachments"
    return hashlib.sha256(data.encode()).hexdigest()[:32]


def get_task_attachment_dir(task_id: int) -> Path:
    """Retourne le répertoire des pièces jointes pour une tâche (créé si besoin)."""
    base = _get_base_dir()
    dir_name = _task_dir_hash(task_id)
    path = base / dir_name
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load_manifest(task_dir: Path) -> dict:
    manifest_path = task_dir / MANIFEST_FILENAME
    if not manifest_path.exists():
        return {}
    try:
        with open(manifest_path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_manifest(task_dir: Path, manifest: dict) -> None:
    manifest_path = task_dir / MANIFEST_FILENAME
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=0)


def _allowed_file_extension(filename: str) -> str | None:
    """Retourne l’extension normalisée si elle est autorisée, sinon None."""
    ext = (Path(filename).suffix or "").lstrip(".").lower()
    if ext in ALLOWED_EXTENSIONS:
        return ext
    return None


def _sanitize_filename(filename: str) -> str:
    """Retourne un nom de fichier sûr (sans chemin, caractères dangereux retirés)."""
    name = Path(filename).name
    name = re.sub(r"[^\w\s\-\.]", "", name, flags=re.UNICODE)
    name = name.strip() or "fichier"
    return name[:200]


def _read_magic(stream, size: int = 32) -> bytes:
    stream.seek(0)
    return stream.read(size)


def _validate_magic(data: bytes, ext: str) -> bool:
    """Vérifie que les premiers octets correspondent au type attendu."""
    sigs = _MAGIC_SIGNATURES.get(ext)
    if sigs is None:
        # CSV : rejeter les fichiers clairement binaires (ex. exécutables renommés en .csv)
        if ext == "csv":
            if not data:
                return True
            # BOM UTF-8 ou premier octet imprimable/ASCII
            if data[:3] == b"\xef\xbb\xbf":
                return True
            return all(b < 128 and (b >= 0x20 or b in (0x09, 0x0A, 0x0D)) for b in data[: min(64, len(data))])
        return True
    if not sigs:
        return True  # tar : extension only
    return any(data.startswith(s) for s in sigs)


def validate_file_upload(stream, filename: str) -> tuple[bool, str]:
    """
    Valide un fichier (extension + magic bytes).
    Retourne (True, "") si OK, (False, message_erreur) sinon.
    """
    ext = _allowed_file_extension(filename)
    if not ext:
        return False, "Type de fichier non autorisé. Autorisés : csv, pdf, zip, doc, docx, xls, xlsx, 7z, tar, gz."

    max_size = current_app.config.get("TASK_ATTACHMENTS_MAX_FILE_SIZE", 25 * 1024 * 1024)
    stream.seek(0, 2)
    size = stream.tell()
    stream.seek(0)
    if size > max_size:
        return False, f"Fichier trop volumineux (max {max_size // (1024*1024)} Mo)."
    if size == 0:
        return False, "Fichier vide."

    magic = _read_magic(stream, 32)
    if not _validate_magic(magic, ext):
        return False, "Le contenu du fichier ne correspond pas à son extension (fichier non autorisé ou corrompu)."
    return True, ""


def list_attachments(task_id: int) -> list[dict]:
    """Liste les pièces jointes d’une tâche (id, name, size, uploaded_at)."""
    task_dir = get_task_attachment_dir(task_id)
    manifest = _load_manifest(task_dir)
    out = []
    for file_id, meta in manifest.items():
        path = task_dir / file_id
        if not path.is_file():
            continue
        out.append(
            {
                "id": file_id,
                "name": meta.get("original_name", "fichier"),
                "size": meta.get("size", 0),
                "uploaded_at": meta.get("uploaded_at", ""),
            }
        )
    out.sort(key=lambda x: x.get("uploaded_at", ""), reverse=True)
    return out


def save_attachment(task_id: int, stream, original_filename: str) -> dict:
    """
    Enregistre une pièce jointe. Valide extension + magic, stocke sous UUID.
    Retourne {"id": uuid, "name": ..., "size": ..., "uploaded_at": ...} ou lève ValueError.
    """
    ok, err = validate_file_upload(stream, original_filename)
    if not ok:
        raise ValueError(err)

    max_per_task = current_app.config.get("TASK_ATTACHMENTS_MAX_FILES_PER_TASK", 50)
    task_dir = get_task_attachment_dir(task_id)
    manifest = _load_manifest(task_dir)
    if len(manifest) >= max_per_task:
        raise ValueError(f"Nombre maximum de pièces jointes atteint ({max_per_task}) pour cette tâche.")

    file_id = str(uuid.uuid4())
    stream.seek(0, 2)
    size = stream.tell()
    stream.seek(0)

    dest = task_dir / file_id
    with open(dest, "wb") as f:
        chunk_size = 65536
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)

    safe_name = _sanitize_filename(original_filename)
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest[file_id] = {
        "original_name": safe_name,
        "size": size,
        "uploaded_at": now,
    }
    _save_manifest(task_dir, manifest)

    return {"id": file_id, "name": safe_name, "size": size, "uploaded_at": now}


def get_attachment_path_and_name(task_id: int, file_id: str) -> tuple[Path, str] | None:
    """
    Retourne (chemin absolu, nom d’affichage) si le fichier existe et appartient à la tâche.
    Sinon None. Vérifie que file_id est un UUID pour éviter path traversal.
    """
    try:
        uuid.UUID(file_id)
    except (ValueError, TypeError):
        return None
    task_dir = get_task_attachment_dir(task_id)
    manifest = _load_manifest(task_dir)
    if file_id not in manifest:
        return None
    path = task_dir / file_id
    if not path.is_file():
        return None
    return (path.resolve(), manifest[file_id].get("original_name", "fichier"))


def delete_attachment(task_id: int, file_id: str) -> bool:
    """Supprime une pièce jointe. Retourne True si supprimée."""
    try:
        uuid.UUID(file_id)
    except (ValueError, TypeError):
        return False
    task_dir = get_task_attachment_dir(task_id)
    manifest = _load_manifest(task_dir)
    if file_id not in manifest:
        return False
    path = task_dir / file_id
    if path.is_file():
        path.unlink()
    del manifest[file_id]
    _save_manifest(task_dir, manifest)
    return True


def delete_task_attachments_folder(task_id: int) -> None:
    """Supprime tout le répertoire des pièces jointes d'une tâche (à appeler lors de la suppression de la tâche)."""
    base = _get_base_dir()
    dir_name = _task_dir_hash(task_id)
    path = base / dir_name
    if path.is_dir():
        try:
            shutil.rmtree(path)
        except OSError as e:
            current_app.logger.warning("Could not remove task attachments folder %s: %s", path, e)
