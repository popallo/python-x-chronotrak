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
    
    # Pour les clients, montrer uniquement les données de leurs clients associés
    if current_user.is_client():
        client_ids = [client.id for client in current_user.clients]
        
        # Statistiques clients
        total_clients = len(current_user.clients)
        
        # Récupérer les projets liés aux clients de l'utilisateur
        projects = Project.query.filter(Project.client_id.in_(client_ids)).all()
        total_projects = len(projects)
        
        # Filtrer les projets avec crédit faible
        projects_low_credit = 0
        low_credit_projects = []
        for project in projects:
            if project.remaining_credit < current_app.config['CREDIT_THRESHOLD']:
                projects_low_credit += 1
                if project.remaining_credit > 0:
                    low_credit_projects.append(project)
        
        low_credit_projects = sorted(low_credit_projects, key=lambda p: p.remaining_credit)[:5]
        
        # Récupérer les tâches liées aux projets
        project_ids = [project.id for project in projects]
        tasks = Task.query.filter(Task.project_id.in_(project_ids)).all()
        total_tasks = len(tasks)
        tasks_todo = sum(1 for task in tasks if task.status == 'à faire')
        tasks_in_progress = sum(1 for task in tasks if task.status == 'en cours')
        tasks_done = sum(1 for task in tasks if task.status == 'terminé')
        
        # Tâches urgentes
        urgent_tasks = Task.query.filter(Task.project_id.in_(project_ids), Task.priority=='urgente', Task.status=='à faire').all()
        
        # Mes tâches en cours
        my_tasks = Task.query.filter(Task.project_id.in_(project_ids), Task.user_id==current_user.id, Task.status=='en cours').all()
        
        # Temps enregistré récemment
        recent_time_entries = TimeEntry.query.join(Task).filter(Task.project_id.in_(project_ids)).order_by(TimeEntry.created_at.desc()).limit(10).all()
    
    # Pour les admins et techniciens, montrer toutes les données
    else:
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