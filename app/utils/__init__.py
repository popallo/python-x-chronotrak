from datetime import datetime, timezone
from app.utils.time_format import format_time
from app.models.client import Client

def get_utc_now():
    """Renvoie la date et l'heure actuelle en UTC avec fuseau horaire explicite"""
    return datetime.now(timezone.utc)

def get_client_choices():
    """Retourne la liste des clients pour un SelectField."""
    return [(client.id, client.name) for client in Client.query.order_by(Client.name).all()]