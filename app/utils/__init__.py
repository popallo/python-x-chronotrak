from datetime import datetime, timezone
from app.utils.time_format import format_time

def get_utc_now():
    """Renvoie la date et l'heure actuelle en UTC avec fuseau horaire explicite"""
    return datetime.now(timezone.utc)