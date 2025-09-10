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
        if form.time_tracking_enabled.data:
            # Convertir les heures en minutes
            initial_credit_minutes = int(round(form.initial_credit.data * 60))
        else:
            initial_credit_minutes = 0
        
        project = Project(
            name=form.name.data,
            description=form.description.data,
            initial_credit=initial_credit_minutes,
            remaining_credit=initial_credit_minutes,  # Initialiser le crédit restant avec le crédit initial
            time_tracking_enabled=form.time_tracking_enabled.data,
            client_id=client_id
        )
        save_to_db(project)
        
        # Créer un log pour le crédit initial si le projet utilise la gestion de temps
        if form.time_tracking_enabled.data and initial_credit_minutes > 0:
            credit_log = CreditLog(
                project_id=project.id,
                amount=initial_credit_minutes,
                note="Crédit initial"
            )
            save_to_db(credit_log)
        
        flash(f'Projet "{form.name.data}" créé avec succès!', 'success')
        return redirect(url_for('projects.project_details', slug_or_id=project.slug))
        
    return render_template('projects/project_form.html', form=form, client=client, title='Nouveau projet')

@projects.route('/projects/<slug_or_id>')
@login_required
def project_details(slug_or_id):
    from app.models.task import TimeEntry, Task
    project = get_project_by_slug_or_id(slug_or_id)
    tasks = project.tasks
    form = DeleteProjectForm()
    
    # Trier les tâches par statut et par position (exclure les tâches archivées)
    tasks_todo = sorted(
        [task for task in tasks if task.status == 'à faire' and not task.is_archived],
        key=lambda t: (t.position, t.created_at)
    )
    tasks_in_progress = sorted(
        [task for task in tasks if task.status == 'en cours' and not task.is_archived],
        key=lambda t: (t.position, t.created_at)
    )
    # Trier les tâches terminées par position puis date de clôture décroissante (exclure les tâches archivées)
    tasks_done = sorted(
        [task for task in tasks if task.status == 'terminé' and not task.is_archived],
        key=lambda t: (t.position, t.completed_at if t.completed_at else datetime.min)
    )
    
    # Créer un historique unifié avec crédits et temps consommés
    history_items = []
    
    # Ajouter les logs de crédit
    for log in project.credit_logs:
        history_items.append({
            'type': 'credit',
            'amount': log.amount,
            'note': log.note,
            'created_at': log.created_at,
            'task': log.task if log.task_id else None,
            'user': None  # Les logs de crédit n'ont pas d'utilisateur associé
        })
    
    # Ajouter les temps consommés
    time_entries = (
        db.session.query(TimeEntry)
        .join(Task)
        .filter(Task.project_id == project.id)
        .all()
    )
    
    for entry in time_entries:
        history_items.append({
            'type': 'time',
            'amount': -entry.minutes,  # Négatif car c'est une consommation
            'note': f"Temps sur '{entry.task.title}'" + (f" - {entry.description}" if entry.description else ""),
            'created_at': entry.created_at,
            'task': entry.task,
            'user': entry.user
        })
    
    # Trier par date de création décroissante
    history_items.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Limiter l'affichage à 10 éléments pour la vue kanban
    history_items_preview = history_items[:10]
    history_items_total = len(history_items)
    
    return render_template('projects/project_detail.html',
                         project=project,
                         tasks_todo=tasks_todo,
                         tasks_in_progress=tasks_in_progress,
                         tasks_done=tasks_done,
                         history_items=history_items_preview,
                         history_items_total=history_items_total,
                         form=form,
                         title=project.name)

@projects.route('/projects/<slug_or_id>/history')
@login_required
def project_history(slug_or_id):
    """Affiche l'historique complet des crédits et débits d'un projet"""
    from app.models.task import TimeEntry, Task
    project = get_project_by_slug_or_id(slug_or_id)
    
    # Récupération des paramètres de filtrage
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Créer un historique unifié avec crédits et temps consommés
    history_items = []
    
    # Ajouter les logs de crédit
    for log in project.credit_logs:
        history_items.append({
            'type': 'credit',
            'amount': log.amount,
            'note': log.note,
            'created_at': log.created_at,
            'task': log.task if log.task_id else None,
            'user': None  # Les logs de crédit n'ont pas d'utilisateur associé
        })
    
    # Ajouter les temps consommés
    time_entries = (
        db.session.query(TimeEntry)
        .join(Task)
        .filter(Task.project_id == project.id)
        .all()
    )
    
    for entry in time_entries:
        history_items.append({
            'type': 'time',
            'amount': -entry.minutes,  # Négatif car c'est une consommation
            'note': f"Temps sur '{entry.task.title}'" + (f" - {entry.description}" if entry.description else ""),
            'created_at': entry.created_at,
            'task': entry.task,
            'user': entry.user
        })
    
    # Trier par date de création décroissante
    history_items.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Pagination manuelle
    total_items = len(history_items)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_items = history_items[start_idx:end_idx]
    
    # Calculer les informations de pagination
    has_prev = page > 1
    has_next = end_idx < total_items
    prev_page = page - 1 if has_prev else None
    next_page = page + 1 if has_next else None
    
    return render_template('projects/project_history.html',
                         project=project,
                         history_items=paginated_items,
                         total_items=total_items,
                         page=page,
                         per_page=per_page,
                         has_prev=has_prev,
                         has_next=has_next,
                         prev_page=prev_page,
                         next_page=next_page,
                         title=f"Historique - {project.name}")

@projects.route('/projects/<slug_or_id>/edit', methods=['GET', 'POST'])
@login_and_admin_required
def edit_project(slug_or_id):
    from app.models.task import TimeEntry, Task
    project = get_project_by_slug_or_id(slug_or_id)
    form = ProjectForm(obj=project)

    # Vérifier s'il existe des temps enregistrés sur ce projet
    any_time_logged = (
        db.session.query(TimeEntry)
        .join(Task)
        .filter(Task.project_id == project.id)
        .count() > 0
    )

    if form.validate_on_submit() and not any_time_logged:
        project.name = form.name.data
        project.description = form.description.data
        project.time_tracking_enabled = form.time_tracking_enabled.data
        
        # Si on active la gestion de temps, on met à jour le crédit initial
        if form.time_tracking_enabled.data:
            # Convertir les heures en minutes
            new_initial_credit = int(round(form.initial_credit.data * 60))
            print(f"DEBUG: form.initial_credit.data = {form.initial_credit.data}")
            print(f"DEBUG: new_initial_credit = {new_initial_credit} minutes")
            print(f"DEBUG: project.initial_credit avant = {project.initial_credit} minutes")
            
            # Calculer la différence pour ajuster le crédit restant
            credit_difference = new_initial_credit - project.initial_credit
            print(f"DEBUG: credit_difference = {credit_difference} minutes")
            
            # Mettre à jour le crédit initial
            project.initial_credit = new_initial_credit
            print(f"DEBUG: project.initial_credit après = {project.initial_credit} minutes")
            
            # Ajuster le crédit restant de la même différence
            project.remaining_credit += credit_difference
            print(f"DEBUG: project.remaining_credit avant ajustement = {project.remaining_credit - credit_difference} minutes")
            print(f"DEBUG: project.remaining_credit après ajustement = {project.remaining_credit} minutes")
            
            # Créer un log si le crédit initial a été modifié
            if credit_difference != 0:
                credit_log = CreditLog(
                    project_id=project.id,
                    amount=credit_difference,
                    note=f"Modification du crédit initial: {credit_difference/60:.1f}h"
                )
                save_to_db(credit_log)
        else:
            # Si on désactive la gestion de temps, on met le crédit à 0
            project.initial_credit = 0
            project.remaining_credit = 0
            
        save_to_db(project)
        
        flash(f'Projet "{project.name}" mis à jour!', 'success')
        return redirect(url_for('projects.project_details', slug_or_id=project.slug))
    elif form.validate_on_submit() and any_time_logged:
        flash("Impossible de modifier le crédit initial : des temps ont déjà été enregistrés sur ce projet.", "warning")

    return render_template('projects/project_form.html', form=form, project=project, title='Modifier le projet', any_time_logged=any_time_logged)

@projects.route('/projects/<slug_or_id>/add_credit', methods=['GET', 'POST'])
@login_and_admin_required
def add_credit(slug_or_id):
    project = get_project_by_slug_or_id(slug_or_id)
    form = AddCreditForm()
    
    if form.validate_on_submit():
        # Convertir les heures en minutes
        amount_minutes = int(round(form.amount.data * 60))
        
        credit_log = CreditLog(
            project_id=project.id,
            amount=amount_minutes,
            note=form.note.data
        )
        project.remaining_credit += amount_minutes
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