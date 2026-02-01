from flask import Blueprint, render_template, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.models.client import Client
from app.models.project import Project
from app.models.task import Task, TimeEntry
from app.models.user import User
from sqlalchemy import func, case
from app import db, cache
from datetime import datetime
from app.utils.route_utils import (
    get_accessible_clients,
    get_accessible_projects,
    get_task_by_id,
    get_project_by_id
)

main = Blueprint('main', __name__)

def get_dashboard_stats():
    """Récupère les statistiques du tableau de bord"""
    # Convertir le seuil de crédit en minutes (il est configuré en heures)
    credit_threshold_minutes = current_app.config['CREDIT_THRESHOLD'] * 60
    today = datetime.utcnow().date()
    
    if current_user.is_client():
        # Pour les clients, montrer uniquement les données de leurs clients associés
        clients_query = get_accessible_clients()
        client_ids = [client.id for client in clients_query.all()]
        
        # Optimisation : requêtes séparées pour éviter les JOINs complexes
        try:
            # Requêtes séparées pour de meilleures performances
            total_clients = db.session.query(func.count(Client.id)).filter(
                Client.id.in_(client_ids)
            ).scalar() or 0
            
            total_projects = db.session.query(func.count(Project.id)).filter(
                Project.client_id.in_(client_ids)
            ).scalar() or 0
            
            total_tasks = db.session.query(func.count(Task.id)).join(Project).filter(
                Project.client_id.in_(client_ids),
                db.or_(Task.scheduled_for.is_(None), Task.scheduled_for <= today)
            ).scalar() or 0
            
            total_time = db.session.query(func.sum(TimeEntry.minutes)).join(Task).join(Project).filter(
                Project.client_id.in_(client_ids)
            ).scalar() or 0
            
            stats = type('Stats', (), {
                'total_clients': total_clients,
                'total_projects': total_projects,
                'total_tasks': total_tasks,
                'total_time': total_time
            })()
                
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la récupération des statistiques: {e}")
            stats = type('Stats', (), {
                'total_clients': 0,
                'total_projects': 0,
                'total_tasks': 0,
                'total_time': 0
            })()
        
        # Requête séparée pour les projets en crédit faible
        projects_low_credit = db.session.query(func.count(Project.id)).filter(
            Project.client_id.in_(client_ids),
            Project.remaining_credit < credit_threshold_minutes,
            Project.remaining_credit > 0
        ).scalar() or 0
        
        # Requête séparée pour les tâches par statut
        tasks_todo = db.session.query(func.count(Task.id)).join(Project).filter(
            Project.client_id.in_(client_ids),
            Task.status == 'à faire',
            db.or_(Task.scheduled_for.is_(None), Task.scheduled_for <= today)
        ).scalar() or 0
        
        tasks_in_progress = db.session.query(func.count(Task.id)).join(Project).filter(
            Project.client_id.in_(client_ids),
            Task.status == 'en cours',
            db.or_(Task.scheduled_for.is_(None), Task.scheduled_for <= today)
        ).scalar() or 0
        
        # S'assurer que les valeurs ne sont pas None
        if stats is None:
            stats = type('Stats', (), {
                'total_clients': 0,
                'total_projects': 0,
                'total_tasks': 0,
                'total_time': 0
            })()
        
        # Récupérer les projets avec crédit faible
        low_credit_projects = Project.query.filter(
            Project.client_id.in_(client_ids),
            Project.remaining_credit < credit_threshold_minutes,
            Project.remaining_credit > 0
        ).order_by(Project.remaining_credit).limit(5).all()
        
        return {
            'total_clients': stats.total_clients or 0,
            'total_projects': stats.total_projects or 0,
            'projects_low_credit': projects_low_credit,
            'low_credit_projects': low_credit_projects,
            'total_tasks': stats.total_tasks or 0,
            'tasks_todo': tasks_todo,
            'tasks_in_progress': tasks_in_progress,
            'total_time': (stats.total_time or 0) / 60  # Convertir en heures
        }
    else:
        # Pour les admins et techniciens - requêtes séparées optimisées
        try:
            # Requêtes séparées pour de meilleures performances
            total_clients = db.session.query(func.count(Client.id)).scalar() or 0
            total_projects = db.session.query(func.count(Project.id)).scalar() or 0
            total_tasks = db.session.query(func.count(Task.id)).filter(
                db.or_(Task.scheduled_for.is_(None), Task.scheduled_for <= today)
            ).scalar() or 0
            
            stats = type('Stats', (), {
                'total_clients': total_clients,
                'total_projects': total_projects,
                'total_tasks': total_tasks
            })()
                
        except Exception as e:
            current_app.logger.error(f"Erreur lors de la récupération des statistiques admin: {e}")
            stats = type('Stats', (), {
                'total_clients': 0,
                'total_projects': 0,
                'total_tasks': 0
            })()
        
        # Requête séparée pour les projets en crédit faible
        projects_low_credit = db.session.query(func.count(Project.id)).filter(
            Project.remaining_credit < credit_threshold_minutes,
            Project.remaining_credit > 0
        ).scalar() or 0
        
        # Requêtes séparées pour les tâches par statut
        tasks_todo = db.session.query(func.count(Task.id)).filter(
            Task.status == 'à faire',
            db.or_(Task.scheduled_for.is_(None), Task.scheduled_for <= today)
        ).scalar() or 0
        
        tasks_in_progress = db.session.query(func.count(Task.id)).filter(
            Task.status == 'en cours',
            db.or_(Task.scheduled_for.is_(None), Task.scheduled_for <= today)
        ).scalar() or 0
        
        tasks_done = db.session.query(func.count(Task.id)).filter(
            Task.status == 'terminé',
            db.or_(Task.scheduled_for.is_(None), Task.scheduled_for <= today)
        ).scalar() or 0
        
        # S'assurer que les valeurs ne sont pas None
        if stats is None:
            stats = type('Stats', (), {
                'total_clients': 0,
                'total_projects': 0,
                'total_tasks': 0
            })()
        
        # Requêtes séparées pour les données détaillées (limitées)
        low_credit_projects = Project.query.filter(
            Project.remaining_credit < credit_threshold_minutes, 
            Project.remaining_credit > 0
        ).order_by(Project.remaining_credit).limit(5).all()
        
        urgent_tasks = Task.query.filter(
            Task.priority == 'urgente',
            Task.status == 'à faire',
            db.or_(Task.scheduled_for.is_(None), Task.scheduled_for <= today)
        ).limit(10).all()
        my_tasks = Task.query.filter(
            Task.user_id == current_user.id,
            Task.status == 'en cours',
            db.or_(Task.scheduled_for.is_(None), Task.scheduled_for <= today)
        ).limit(10).all()
        recent_time_entries = TimeEntry.query.order_by(TimeEntry.created_at.desc()).limit(10).all()
        
        return {
            'total_clients': stats.total_clients or 0,
            'total_projects': stats.total_projects or 0,
            'projects_low_credit': projects_low_credit,
            'low_credit_projects': low_credit_projects,
            'total_tasks': stats.total_tasks or 0,
            'tasks_todo': tasks_todo,
            'tasks_in_progress': tasks_in_progress,
            'tasks_done': tasks_done,
            'urgent_tasks': urgent_tasks,
            'my_tasks': my_tasks,
            'recent_time_entries': recent_time_entries
        }

@main.route('/')
def index():
    """Page d'accueil pour les utilisateurs non connectés"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html', title='Bienvenue')

@main.route('/dashboard')
@login_required
def dashboard():
    """Tableau de bord principal"""
    stats = get_dashboard_stats()
    return render_template('dashboard.html', **stats, title='Tableau de bord')

@main.route('/reports')
@login_required
def reports():
    """Page des rapports"""
    # Temps total enregistré par projet
    project_times = db.session.query(
        Project.name, 
        func.sum(TimeEntry.minutes / 60.0).label('total_hours')
    ).join(
        Task, Task.project_id == Project.id
    ).join(
        TimeEntry, TimeEntry.task_id == Task.id
    ).group_by(Project.name).all()
    
    # Temps enregistré par utilisateur
    user_times = db.session.query(
        User.name,
        func.sum(TimeEntry.minutes / 60.0).label('total_hours')
    ).join(
        TimeEntry, TimeEntry.user_id == User.id
    ).group_by(User.name).all()
    
    # Temps enregistré par mois
    monthly_times = db.session.query(
        func.strftime('%Y-%m', TimeEntry.created_at).label('month'),
        func.sum(TimeEntry.minutes / 60.0).label('total_hours')
    ).group_by('month').order_by('month').all()
    
    return render_template('reports.html',
                         project_times=project_times,
                         user_times=user_times,
                         monthly_times=monthly_times,
                         title='Rapports')