from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.communication import Communication
from app.models.user import User
from app.models.task import Task
from app.models.project import Project
from app.utils.decorators import login_and_admin_required
from app.utils.route_utils import (
    get_communication_by_id,
    get_user_by_id,
    get_task_by_id,
    get_project_by_id,
    apply_filters,
    apply_sorting
)
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from app.utils import get_utc_now

communications = Blueprint('communications', __name__)

def get_communication_stats():
    """Récupère les statistiques des communications"""
    # Convertir en datetime naive pour la comparaison avec les datetimes de la DB (SQLite)
    now = get_utc_now().replace(tzinfo=None)
    return {
        'total': Communication.query.count(),
        'last_24h': Communication.query.filter(
            Communication.sent_at >= now - timedelta(days=1)
        ).count(),
        'last_7d': Communication.query.filter(
            Communication.sent_at >= now - timedelta(days=7)
        ).count()
    }

@communications.route('/admin/communications')
@login_and_admin_required
def list_communications():
    """Liste des communications envoyées"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Récupérer les filtres
    filters = {
        'type': request.args.get('type'),
        'recipient': request.args.get('recipient'),
        'date_from': request.args.get('date_from'),
        'date_to': request.args.get('date_to')
    }
    
    # Construction de la requête de base
    query = Communication.query
    
    # Appliquer les filtres
    query, filters_active = apply_filters(query, Communication, filters)
    
    # Tri par date d'envoi (plus récent d'abord)
    query = query.order_by(desc(Communication.sent_at))
    
    # Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    communications = pagination.items
    
    # Types de communications pour le filtre
    communication_types = db.session.query(Communication.type).distinct().all()
    communication_types = [t[0] for t in communication_types]
    
    # Statistiques
    stats = get_communication_stats()
    
    return render_template('admin/communications.html', 
                         communications=communications,
                         pagination=pagination,
                         communication_types=communication_types,
                         stats=stats,
                         filters_active=filters_active,
                         title='Suivi des communications')
    
@communications.route('/admin/communications/<int:comm_id>')
@login_and_admin_required
def view_communication(comm_id):
    """Voir le détail d'une communication"""
    comm = get_communication_by_id(comm_id)
    
    # Récupérer les entités liées si elles existent
    user = get_user_by_id(comm.user_id) if comm.user_id else None
    task = get_task_by_id(comm.task_id) if comm.task_id else None
    project = get_project_by_id(comm.project_id) if comm.project_id else None
    triggered_by = get_user_by_id(comm.triggered_by_id) if comm.triggered_by_id else None
    
    return render_template('admin/communication_detail.html',
                         comm=comm,
                         user=user,
                         task=task,
                         project=project,
                         triggered_by=triggered_by,
                         title='Détail de la communication')