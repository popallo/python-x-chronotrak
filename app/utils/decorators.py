from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user, login_required


def client_required(f):
    """Vérifie si l'utilisateur est un administrateur, un technicien ou un client avec accès"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Les administrateurs et techniciens ont accès à tout
        if current_user.is_admin() or current_user.is_technician():
            return f(*args, **kwargs)

        # Pour les clients, vérifier l'accès selon le contexte
        client_id = kwargs.get("client_id")
        if client_id and current_user.is_client():
            if current_user.has_access_to_client(client_id):
                return f(*args, **kwargs)
            else:
                flash("Vous n'avez pas accès à ce client.", "danger")
                return redirect(url_for("main.dashboard"))

        # Pour les projets, vérifier si le projet appartient à un client auquel l'utilisateur a accès
        project_id = kwargs.get("project_id")
        if project_id and current_user.is_client():
            from app.models.project import Project

            project = Project.query.get_or_404(project_id)
            if current_user.has_access_to_client(project.client_id):
                return f(*args, **kwargs)
            else:
                flash("Vous n'avez pas accès à ce projet.", "danger")
                return redirect(url_for("main.dashboard"))

        # Si on arrive ici, c'est qu'aucune condition n'a été remplie
        if current_user.is_client():
            flash("Vous n'avez pas les permissions nécessaires pour accéder à cette page.", "danger")
            return redirect(url_for("main.dashboard"))

        # Pour tout autre cas (par exemple, pas de client_id ni project_id dans l'URL)
        abort(403)

    return decorated_function


# app/utils/decorators.py (ajout)
def admin_required(f):
    """Vérifie si l'utilisateur est un administrateur"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash("Accès refusé. Vous devez être administrateur pour accéder à cette page.", "danger")
            return redirect(url_for("main.dashboard"))
        return f(*args, **kwargs)

    return decorated_function


def login_and_client_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        # Les administrateurs et techniciens ont accès à tout
        if current_user.is_admin() or current_user.is_technician():
            return f(*args, **kwargs)

        # Pour les clients, vérifier l'accès selon le contexte
        client_id = kwargs.get("client_id")
        if client_id and current_user.is_client():
            if current_user.has_access_to_client(client_id):
                return f(*args, **kwargs)
            else:
                flash("Vous n'avez pas accès à ce client.", "danger")
                return redirect(url_for("main.dashboard"))

        # Pour les projets, vérifier si le projet appartient à un client auquel l'utilisateur a accès
        project_id = kwargs.get("project_id")
        slug_or_id = kwargs.get("slug_or_id")
        if (project_id or slug_or_id) and current_user.is_client():
            from app.models.project import Project

            if slug_or_id:
                from app.utils.route_utils import get_project_by_slug_or_id

                project = get_project_by_slug_or_id(slug_or_id)
            else:
                project = Project.query.get_or_404(project_id)
            if current_user.has_access_to_client(project.client_id):
                return f(*args, **kwargs)
            else:
                flash("Vous n'avez pas accès à ce projet.", "danger")
                return redirect(url_for("main.dashboard"))

        # Si on arrive ici, c'est qu'aucune condition n'a été remplie
        if current_user.is_client():
            flash("Vous n'avez pas les permissions nécessaires pour accéder à cette page.", "danger")
            return redirect(url_for("main.dashboard"))

        # Pour tout autre cas (par exemple, pas de client_id ni project_id dans l'URL)
        abort(403)

    return decorated_function


def login_and_admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)

    return decorated_function
