from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models.project import Project, CreditLog
from app.models.client import Client
from app.forms.project import ProjectForm, AddCreditForm, DeleteProjectForm
from app.utils.decorators import login_and_client_required, login_and_admin_required
from app.utils.route_utils import (
    get_project_by_id,
    get_project_by_slug_or_id,
    get_client_by_id,
    get_accessible_projects,
    save_to_db,
    delete_from_db,
    apply_filters,
    apply_sorting
)
from datetime import datetime
from sqlalchemy import or_, and_, func
from app.models.task import Task

projects = Blueprint('projects', __name__)

@projects.route('/projects')
@login_required
def list_projects():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Récupérer les filtres
    filters = {
        'search': request.args.get('search'),
        'client_id': request.args.get('client_id', type=int)
    }
    
    # Appliquer les filtres
    query = get_accessible_projects()
    query, filters_active = apply_filters(query, Project, filters)
    
    # Appliquer le tri
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')
    query = apply_sorting(query, Project, sort_by, sort_order)
    
    projects = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Récupérer la liste des clients pour le filtre
    clients = Client.query.all() if current_user.is_admin() or current_user.is_technician() else current_user.clients
    
    return render_template('projects/projects.html', 
                         projects=projects,
                         clients=clients,
                         filters_active=filters_active,
                         sort_by=sort_by,
                         sort_order=sort_order,
                         pagination=projects,
                         title='Projets')

@projects.route('/clients/<int:client_id>/projects/new', methods=['GET', 'POST'])
@login_required
def new_project(client_id):
    client = get_client_by_id(client_id)
    if current_user.is_client() and not current_user.has_access_to_client(client_id):
        abort(403)
        
    form = ProjectForm()
    if form.validate_on_submit():
        # Si la gestion de temps est désactivée, on met le crédit à 0
        initial_credit = form.initial_credit.data if form.time_tracking_enabled.data else 0
        
        project = Project(
            name=form.name.data,
            description=form.description.data,
            initial_credit=initial_credit,
            time_tracking_enabled=form.time_tracking_enabled.data,
            client_id=client_id
        )
        save_to_db(project)
        flash(f'Projet "{form.name.data}" créé avec succès!', 'success')
        return redirect(url_for('projects.project_details', slug_or_id=project.slug))
        
    return render_template('projects/project_form.html', form=form, client=client, title='Nouveau projet')

@projects.route('/projects/<slug_or_id>')
@login_required
def project_details(slug_or_id):
    project = get_project_by_slug_or_id(slug_or_id)
    tasks = project.tasks
    form = DeleteProjectForm()
    
    # Trier les tâches par statut
    tasks_todo = [task for task in tasks if task.status == 'à faire']
    tasks_in_progress = [task for task in tasks if task.status == 'en cours']
    # Trier les tâches terminées par date de clôture décroissante
    tasks_done = sorted(
        [task for task in tasks if task.status == 'terminé'],
        key=lambda x: x.completed_at if x.completed_at else datetime.min,
        reverse=True
    )
    
    # Trier les logs de crédit par date de création décroissante
    credit_logs = sorted(project.credit_logs, key=lambda x: x.created_at, reverse=True)
    
    return render_template('projects/project_detail.html',
                         project=project,
                         tasks_todo=tasks_todo,
                         tasks_in_progress=tasks_in_progress,
                         tasks_done=tasks_done,
                         credit_logs=credit_logs,
                         form=form,
                         title=project.name)

@projects.route('/projects/<slug_or_id>/edit', methods=['GET', 'POST'])
@login_and_admin_required
def edit_project(slug_or_id):
    project = get_project_by_slug_or_id(slug_or_id)
    form = ProjectForm(obj=project)
    
    if form.validate_on_submit():
        project.name = form.name.data
        project.description = form.description.data
        project.time_tracking_enabled = form.time_tracking_enabled.data
        
        # Si on active la gestion de temps, on met à jour le crédit initial
        if form.time_tracking_enabled.data:
            project.initial_credit = form.initial_credit.data
        else:
            # Si on désactive la gestion de temps, on met le crédit à 0
            project.initial_credit = 0
            project.remaining_credit = 0
            
        save_to_db(project)
        
        flash(f'Projet "{project.name}" mis à jour!', 'success')
        return redirect(url_for('projects.project_details', slug_or_id=project.slug))
    
    return render_template('projects/project_form.html', form=form, project=project, title='Modifier le projet')

@projects.route('/projects/<slug_or_id>/add_credit', methods=['GET', 'POST'])
@login_and_admin_required
def add_credit(slug_or_id):
    project = get_project_by_slug_or_id(slug_or_id)
    form = AddCreditForm()
    
    if form.validate_on_submit():
        credit_log = CreditLog(
            project_id=project.id,
            amount=form.amount.data,
            note=form.note.data
        )
        project.remaining_credit += form.amount.data
        save_to_db(credit_log)
        save_to_db(project)
        
        flash(f'Crédit ajouté avec succès!', 'success')
        return redirect(url_for('projects.project_details', slug_or_id=project.slug))
    
    return render_template('projects/add_credit.html', form=form, project=project)

@projects.route('/projects/<slug_or_id>/delete', methods=['POST'])
@login_and_admin_required
def delete_project(slug_or_id):
    project = get_project_by_slug_or_id(slug_or_id)
    delete_from_db(project)
    flash(f'Projet "{project.name}" supprimé!', 'success')
    return redirect(url_for('projects.list_projects'))