"""Limitation du taux de tentatives de connexion par adresse IP."""

from flask import Request, current_app

from app import cache

_CLIENT_IP_HEADERS = (
    "CF-Connecting-IP",
    "X-Real-IP",
    "X-Forwarded-For",
    "X-Client-IP",
    "X-Forwarded",
    "Forwarded-For",
    "Forwarded",
)


def get_client_ip(req: Request) -> str:
    """Retourne l'adresse IP du client en tenant compte des proxies."""
    for header in _CLIENT_IP_HEADERS:
        ip = req.headers.get(header)
        if ip:
            return ip.split(",")[0].strip()
    return req.remote_addr or "unknown"


def _cache_key(client_ip: str) -> str:
    prefix = current_app.config.get("CACHE_KEY_PREFIX", "chronotrak_")
    return f"{prefix}login_attempts:{client_ip}"


def is_login_rate_limited(client_ip: str) -> bool:
    """Indique si l'adresse IP a dépassé le nombre de tentatives autorisées."""
    if not current_app.config.get("LOGIN_RATE_LIMIT_ENABLED", True):
        return False

    max_attempts = current_app.config.get("LOGIN_RATE_LIMIT_MAX_ATTEMPTS", 5)
    attempts = cache.get(_cache_key(client_ip)) or 0
    return attempts >= max_attempts


def record_failed_login(client_ip: str) -> None:
    """Enregistre une tentative de connexion échouée pour une adresse IP."""
    if not current_app.config.get("LOGIN_RATE_LIMIT_ENABLED", True):
        return

    key = _cache_key(client_ip)
    window = current_app.config.get("LOGIN_RATE_LIMIT_WINDOW", 900)
    attempts = cache.get(key) or 0
    cache.set(key, attempts + 1, timeout=window)


def clear_login_attempts(client_ip: str) -> None:
    """Réinitialise le compteur de tentatives après une connexion réussie."""
    cache.delete(_cache_key(client_ip))
