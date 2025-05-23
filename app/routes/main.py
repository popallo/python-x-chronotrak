from flask import Blueprint, render_template, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.models.client import Client
from app.models.project import Project
from app.models.task import Task, TimeEntry
from app.models.user import User
from sqlalchemy import func, case
from app import db
from app.utils.route_utils import (
    get_accessible_clients,
    get_accessible_projects,
    get_task_by_id,
    get_project_by_id
)

main = Blueprint('main', __name__)

def get_dashboard_stats():
    """Récupère les statistiques du tableau de bord"""
    if current_user.is_client():
        # Pour les clients, montrer uniquement les données de leurs clients associés
        clients_query = get_accessible_clients()
        client_ids = [client.id for client in clients_query.all()]
        
        # Statistiques clients et projets en une seule requête
        stats = db.session.query(
            func.count(Client.id).label('total_clients'),
            func.count(Project.id).label('total_projects'),
            func.sum(case((Project.remaining_credit < current_app.config['CREDIT_THRESHOLD'], 1), else_=0)).label('projects_low_credit')
        ).join(Project, Project.client_id == Client.id, isouter=True).filter(Client.id.in_(client_ids)).first()
        
        total_clients = stats.total_clients or 0
        total_projects = stats.total_projects or 0
        projects_low_credit = stats.projects_low_credit or 0
        
        # Récupérer les projets avec crédit faible en une seule requête
        low_credit_projects = Project.query.filter(
            Project.client_id.in_(client_ids),
            Project.remaining_credit < current_app.config['CREDIT_THRESHOLD'],
            Project.remaining_credit > 0
        ).order_by(Project.remaining_credit).limit(5).all()
        
        # Statistiques des tâches en une seule requête
        task_stats = db.session.query(
            func.count(Task.id).label('total_tasks'),
            func.sum(case((Task.status == 'à faire', 1), else_=0)).label('tasks_todo'),
            func.sum(case((Task.status == 'en cours', 1), else_=0)).label('tasks_in_progress')
        ).join(Project, Task.project_id == Project.id).filter(Project.client_id.in_(client_ids)).first()
        
        total_tasks = task_stats.total_tasks or 0
        tasks_todo = task_stats.tasks_todo or 0
        tasks_in_progress = task_stats.tasks_in_progress or 0
        
        # Temps total en une seule requête
        total_time = db.session.query(
            func.sum(TimeEntry.hours).label('total_time')
        ).join(Task, TimeEntry.task_id == Task.id).join(Project, Task.project_id == Project.id).filter(
            Project.client_id.in_(client_ids)
        ).scalar() or 0
        
        return {
            'total_clients': total_clients,
            'total_projects': total_projects,
            'projects_low_credit': projects_low_credit,
            'low_credit_projects': low_credit_projects,
            'total_tasks': total_tasks,
            'tasks_todo': tasks_todo,
            'tasks_in_progress': tasks_in_progress,
            'total_time': total_time
        }
    else:
        # Pour les admins et techniciens, montrer toutes les données
        total_clients = Client.query.count()
        total_projects = Project.query.count()
        
        projects_low_credit = Project.query.filter(Project.remaining_credit < current_app.config['CREDIT_THRESHOLD']).count()
        
        low_credit_projects = Project.query.filter(
            Project.remaining_credit < current_app.config['CREDIT_THRESHOLD'], 
            Project.remaining_credit > 0
        ).order_by(Project.remaining_credit).limit(5).all()
        
        total_tasks = Task.query.count()
        tasks_todo = Task.query.filter_by(status='à faire').count()
        tasks_in_progress = Task.query.filter_by(status='en cours').count()
        tasks_done = Task.query.filter_by(status='terminé').count()
        
        urgent_tasks = Task.query.filter_by(priority='urgente', status='à faire').all()
        my_tasks = Task.query.filter_by(user_id=current_user.id, status='en cours').all()
        recent_time_entries = TimeEntry.query.order_by(TimeEntry.created_at.desc()).limit(10).all()
    
    return {
        'total_clients': total_clients,
        'total_projects': total_projects,
        'projects_low_credit': projects_low_credit,
        'low_credit_projects': low_credit_projects,
        'total_tasks': total_tasks,
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
        func.sum(TimeEntry.hours).label('total_hours')
    ).join(
        Task, Task.project_id == Project.id
    ).join(
        TimeEntry, TimeEntry.task_id == Task.id
    ).group_by(Project.name).all()
    
    # Temps enregistré par utilisateur
    user_times = db.session.query(
        User.name,
        func.sum(TimeEntry.hours).label('total_hours')
    ).join(
        TimeEntry, TimeEntry.user_id == User.id
    ).group_by(User.name).all()
    
    # Temps enregistré par mois
    monthly_times = db.session.query(
        func.strftime('%Y-%m', TimeEntry.created_at).label('month'),
        func.sum(TimeEntry.hours).label('total_hours')
    ).group_by('month').order_by('month').all()
    
    return render_template('reports.html',
                         project_times=project_times,
                         user_times=user_times,
                         monthly_times=monthly_times,
                         title='Rapports')