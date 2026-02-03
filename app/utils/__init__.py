from datetime import UTC, datetime

from flask import flash

from app.utils.time_format import format_time as format_time


def get_utc_now():
    """Renvoie la date et l'heure actuelle en UTC avec fuseau horaire explicite"""
    return datetime.now(UTC)


def get_client_choices():
    """Retourne la liste des clients pour un SelectField."""
    from app.models.client import Client

    return [(client.id, client.name) for client in Client.query.order_by(Client.name).all()]


def get_accessible_clients(user):
    """Retourne la liste des clients accessibles pour un utilisateur donné."""
    from app.models.client import Client

    if user.is_admin() or user.is_technician():
        return Client.query.order_by(Client.name).all()
    return user.clients


def flash_admin_required():
    flash("Accès refusé. Droits administrateur requis.", "danger")


def flash_already_logged_in():
    flash("Vous êtes déjà connecté.", "info")


def flash_cannot_delete_self():
    flash("Vous ne pouvez pas supprimer votre propre compte.", "danger")
