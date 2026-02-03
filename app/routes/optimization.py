"""
Route simple pour afficher les optimisations Python 3.13
"""

from app.utils.python313_optimizations import get_python313_info
from flask import Blueprint, jsonify, render_template
from flask_login import current_user, login_required

optimization = Blueprint("optimization", __name__)


@optimization.route("/optimization/status")
@login_required
def status():
    """Affiche le statut des optimisations Python 3.13"""

    # Vérifier les permissions admin
    if not current_user.is_admin:
        return "Accès refusé", 403

    info = get_python313_info()

    return render_template("admin/optimization_status.html", python_info=info)


@optimization.route("/api/optimization/stats")
@login_required
def api_stats():
    """API pour récupérer les informations d'optimisation"""

    if not current_user.is_admin:
        return jsonify({"error": "Accès refusé"}), 403

    return jsonify({"python_info": get_python313_info()})
