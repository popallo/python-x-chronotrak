from flask import Blueprint, render_template, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.models.client import Client
from app.models.project import Project
from app.models.task import Task, TimeEntry
from app.models.user import User
from sqlalchemy import func
from app import db

main = Blueprint('main', __name__)

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
    
    # Statistiques clients
    total_clients = Client.query.count()
    
    # Statistiques projets
    total_projects = Project.query.count()
    
    projects_low_credit = Project.query.filter(Project.remaining_credit < current_app.config['CREDIT_THRESHOLD']).count()
    
    low_credit_projects = Project.query.filter(
        Project.remaining_credit < current_app.config['CREDIT_THRESHOLD'], 
        Project.remaining_credit > 0
    ).order_by(Project.remaining_credit).limit(5).all()
    
    # Statistiques tâches
    total_tasks = Task.query.count()
    tasks_todo = Task.query.filter_by(status='à faire').count()
    tasks_in_progress = Task.query.filter_by(status='en cours').count()
    tasks_done = Task.query.filter_by(status='terminé').count()
    
    # Tâches urgentes
    urgent_tasks = Task.query.filter_by(priority='urgente', status='à faire').all()
    
    # Mes tâches en cours (pour l'utilisateur connecté)
    my_tasks = Task.query.filter_by(user_id=current_user.id, status='en cours').all()
    
    # Temps enregistré récemment
    recent_time_entries = TimeEntry.query.order_by(TimeEntry.created_at.desc()).limit(10).all()
    
    return render_template('dashboard.html',
                          total_clients=total_clients,
                          total_projects=total_projects,
                          projects_low_credit=projects_low_credit,
                          low_credit_projects=low_credit_projects,
                          total_tasks=total_tasks,
                          tasks_todo=tasks_todo,
                          tasks_in_progress=tasks_in_progress,
                          tasks_done=tasks_done,
                          urgent_tasks=urgent_tasks,
                          my_tasks=my_tasks,
                          recent_time_entries=recent_time_entries,
                          title='Tableau de bord')

@main.route('/reports')
@login_required
def reports():
    """Page de rapports"""
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