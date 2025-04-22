from datetime import datetime, timezone

def get_utc_now():
    """Renvoie la date et l'heure actuelle en UTC avec fuseau horaire explicite"""
    return datetime.now(timezone.utc)