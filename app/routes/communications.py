from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.communication import Communication
from app.models.user import User
from app.models.task import Task
from app.models.project import Project
from app.utils.decorators import admin_required
from sqlalchemy import desc
from datetime import datetime, timedelta

communications = Blueprint('communications', __name__)

@communications.route('/admin/communications')
@login_required
@admin_required
def list_communications():
    """Liste des communications envoyées"""
    # Paramètres de filtre et pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filtres
    type_filter = request.args.get('type')
    recipient_filter = request.args.get('recipient')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Construction de la requête de base
    query = Communication.query
    
    # Appliquer les filtres
    if type_filter:
        query = query.filter(Communication.type == type_filter)
    
    if recipient_filter:
        query = query.filter(Communication.recipient.ilike(f'%{recipient_filter}%'))
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Communication.sent_at >= date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            # Ajouter 23:59:59 pour inclure toute la journée
            date_to = date_to.replace(hour=23, minute=59, second=59)
            query = query.filter(Communication.sent_at <= date_to)
        except ValueError:
            pass
    
    # Tri par date d'envoi (plus récent d'abord)
    query = query.order_by(desc(Communication.sent_at))
    
    # Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    communications = pagination.items
    
    # Types de communications pour le filtre
    comm_types = db.session.query(Communication.type).distinct().all()
    communication_types = [t[0] for t in comm_types]
    
    # Statistiques
    stats = {
        'total': Communication.query.count(),
        'last_24h': Communication.query.filter(
            Communication.sent_at >= datetime.utcnow() - timedelta(days=1)
        ).count(),
        'last_7d': Communication.query.filter(
            Communication.sent_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
    }
    
    return render_template('admin/communications.html', 
                          communications=communications,
                          pagination=pagination,
                          communication_types=communication_types,
                          stats=stats,
                          title='Suivi des communications')
    
@communications.route('/admin/communications/<int:comm_id>')
@login_required
@admin_required
def view_communication(comm_id):
    """Voir le détail d'une communication"""
    comm = Communication.query.get_or_404(comm_id)
    
    # Récupérer les entités liées si elles existent
    user = User.query.get(comm.user_id) if comm.user_id else None
    task = Task.query.get(comm.task_id) if comm.task_id else None
    project = Project.query.get(comm.project_id) if comm.project_id else None
    triggered_by = User.query.get(comm.triggered_by_id) if comm.triggered_by_id else None
    
    return render_template('admin/communication_detail.html',
                          comm=comm,
                          user=user,
                          task=task,
                          project=project,
                          triggered_by=triggered_by,
                          title='Détail de la communication')