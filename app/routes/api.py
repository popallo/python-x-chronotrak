from app.models.user import User
from app.utils.route_utils import get_project_by_slug_or_id
from flask import Blueprint, current_app, jsonify
from flask_login import current_user, login_required

api = Blueprint("api", __name__, url_prefix="/api")


@api.route("/projects/<slug_or_id>/mentionable-users")
@login_required
def get_mentionable_users(slug_or_id):
    """Récupère la liste des utilisateurs mentionnables pour un projet"""
    current_app.logger.info(f"Recherche du projet avec slug_or_id: {slug_or_id}")

    project = get_project_by_slug_or_id(slug_or_id)
    current_app.logger.info(f"Projet trouvé: {project.name} (ID: {project.id})")

    # Vérifier l'accès au projet
    if current_user.is_client() and not current_user.has_access_to_client(project.client_id):
        current_app.logger.warning(f"Accès refusé pour l'utilisateur {current_user.id} au projet {project.id}")
        return jsonify({"error": "Accès non autorisé"}), 403

    # Récupérer tous les utilisateurs mentionnables
    mentionable_users = []

    # Ajouter les techniciens et administrateurs
    staff_users = User.query.filter(User.role.in_(["technician", "admin"])).all()
    current_app.logger.info(f"Nombre d'utilisateurs staff trouvés: {len(staff_users)}")

    for user in staff_users:
        mentionable_users.append({"id": user.id, "name": user.name, "role": user.role, "email": user.email})

    # Ajouter les utilisateurs clients liés au projet
    client_users = User.query.filter_by(role="client").all()
    current_app.logger.info(f"Nombre d'utilisateurs clients trouvés: {len(client_users)}")

    for user in client_users:
        if user.has_access_to_client(project.client_id):
            mentionable_users.append({"id": user.id, "name": user.name, "role": user.role, "email": user.email})

    current_app.logger.info(f"Nombre total d'utilisateurs mentionnables: {len(mentionable_users)}")
    return jsonify(mentionable_users)
