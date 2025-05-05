from datetime import datetime, timezone
from app.utils.time_format import format_time
from app.models.client import Client
from flask import flash

def get_utc_now():
    """Renvoie la date et l'heure actuelle en UTC avec fuseau horaire explicite"""
    return datetime.now(timezone.utc)

def get_client_choices():
    """Retourne la liste des clients pour un SelectField."""
    return [(client.id, client.name) for client in Client.query.order_by(Client.name).all()]

def get_accessible_clients(user):
    """Retourne la liste des clients accessibles pour un utilisateur donné."""
    if user.is_admin() or user.is_technician():
        return Client.query.order_by(Client.name).all()
    return user.clients

def flash_admin_required():
    flash('Accès refusé. Droits administrateur requis.', 'danger')

def flash_already_logged_in():
    flash('Vous êtes déjà connecté.', 'info')

def flash_cannot_delete_self():
    flash('Vous ne pouvez pas supprimer votre propre compte.', 'danger')