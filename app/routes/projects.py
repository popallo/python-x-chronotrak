from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.project import Project, CreditLog
from app.models.client import Client
from app.forms.project import ProjectForm, AddCreditForm
from app.utils.decorators import login_and_client_required
from app.utils.route_utils import (
    get_client_by_id, 
    get_project_by_id, 
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
        'client_id': request.args.get('client_id', type=int),
        'credit_status': request.args.get('credit_status'),
        'search': request.args.get('search')
    }
    
    # Appliquer les filtres
    query = get_accessible_projects()
    query, filters_active = apply_filters(query, Project, filters)
    
    # Appliquer le tri
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')
    query = apply_sorting(query, Project, sort_by, sort_order)
    
    projects = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('projects/projects.html', 
                         projects=projects,
                         filters_active=filters_active,
                         sort_by=sort_by,
                         sort_order=sort_order)

@projects.route('/clients/<int:client_id>/projects/new', methods=['GET', 'POST'])
@login_and_client_required
def new_project(client_id):
    client = get_client_by_id(client_id)
    form = ProjectForm()
    
    if form.validate_on_submit():
        project = Project(
            name=form.name.data,
            description=form.description.data,
            client_id=client.id,
            initial_credit=form.initial_credit.data,
            remaining_credit=form.initial_credit.data
        )
        save_to_db(project)
        
        flash(f'Projet "{form.name.data}" créé avec succès!', 'success')
        return redirect(url_for('projects.list_projects'))
    
    return render_template('projects/project_form.html', form=form, client=client, title='Nouveau projet')

@projects.route('/projects/<int:project_id>')
@login_and_client_required
def project_details(project_id):
    project = get_project_by_id(project_id)
    
    # Récupérer les tâches par statut
    tasks_query = Task.query.filter_by(project_id=project.id)
    tasks_todo = tasks_query.filter_by(status='à faire').all()
    tasks_in_progress = tasks_query.filter_by(status='en cours').all()
    tasks_done = tasks_query.filter_by(status='terminé').order_by(Task.completed_at.desc()).all()
    
    return render_template('projects/project_detail.html', 
                         project=project,
                         tasks_todo=tasks_todo,
                         tasks_in_progress=tasks_in_progress,
                         tasks_done=tasks_done)

@projects.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_and_client_required
def edit_project(project_id):
    project = get_project_by_id(project_id)
    form = ProjectForm(obj=project)
    
    if form.validate_on_submit():
        project.name = form.name.data
        project.description = form.description.data
        save_to_db(project)
        
        flash(f'Projet "{project.name}" mis à jour!', 'success')
        return redirect(url_for('projects.project_details', project_id=project.id))
    
    return render_template('projects/project_form.html', form=form, project=project, title='Modifier le projet')

@projects.route('/projects/<int:project_id>/add_credit', methods=['GET', 'POST'])
@login_and_client_required
def add_credit(project_id):
    project = get_project_by_id(project_id)
    form = AddCreditForm()
    
    if form.validate_on_submit():
        credit_log = CreditLog(
            project_id=project.id,
            amount=form.amount.data,
            description=form.description.data
        )
        project.remaining_credit += form.amount.data
        save_to_db(credit_log)
        save_to_db(project)
        
        flash(f'Crédit ajouté avec succès!', 'success')
        return redirect(url_for('projects.project_details', project_id=project.id))
    
    return render_template('projects/add_credit.html', form=form, project=project)

@projects.route('/projects/<int:project_id>/delete', methods=['POST'])
@login_and_client_required
def delete_project(project_id):
    project = get_project_by_id(project_id)
    delete_from_db(project)
    flash(f'Projet "{project.name}" supprimé!', 'success')
    return redirect(url_for('projects.list_projects'))