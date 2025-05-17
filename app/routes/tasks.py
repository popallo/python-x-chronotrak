from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import case
from datetime import datetime, timezone
from app import db
from app.models.task import Task, TimeEntry, Comment
from app.models.project import Project
from app.models.client import Client
from app.models.user import User
from app.forms.task import TaskForm, TimeEntryForm, CommentForm, EditCommentForm, DeleteTaskForm
from app.utils import get_utc_now
from app.utils.decorators import login_and_client_required, login_and_admin_required
from app.utils.route_utils import (
    get_project_by_slug_or_id, 
    get_task_by_slug_or_id,
    save_to_db, 
    delete_from_db,
    apply_filters,
    apply_sorting
)
from flask_wtf import FlaskForm

tasks = Blueprint('tasks', __name__)

@tasks.route('/tasks')
@login_required
def list_tasks():
    """Liste toutes les tâches avec filtres et pagination"""
    # Récupération des paramètres de filtrage
    status = request.args.getlist('status')
    priority = request.args.get('priority')
    project_id = request.args.get('project_id', type=int)
    user_id = request.args.get('user_id', type=int)
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Construction de la requête de base
    query = Task.query

    # Filtres
    if status:
        query = query.filter(Task.status.in_(status))
    if priority:
        query = query.filter(Task.priority == priority)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if user_id:
        query = query.filter(Task.user_id == user_id)
    if search:
        query = query.filter(Task.title.ilike(f'%{search}%'))

    # Tri par défaut : date de création décroissante
    query = query.order_by(Task.created_at.desc())

    # Pagination
    tasks = query.paginate(page=page, per_page=per_page, error_out=False)

    # Récupération des données pour les filtres
    projects = Project.query.all()
    users = User.query.filter_by(role='technician').all()

    # Préparation des paramètres de requête pour la pagination
    query_params = {k: v for k, v in request.args.items() if k != 'page'}

    return render_template('tasks/tasks.html',
                         tasks=tasks,
                         projects=projects,
                         users=users,
                         query_params=query_params)

@tasks.route('/projects/<slug_or_id>/tasks/new', methods=['GET', 'POST'])
@login_and_client_required
def new_task(slug_or_id):
    project = get_project_by_slug_or_id(slug_or_id)
    form = TaskForm(current_user=current_user)
    
    if form.validate_on_submit():
        user_id = form.user_id.data if form.user_id.data != 0 else None
        
        # Convertir 0.0 (valeur pour "Non défini") à None
        estimated_time = None if form.estimated_time.data == 0.0 else form.estimated_time.data
        
        task = Task(
            title=form.title.data,
            description=form.description.data,
            status=form.status.data,
            priority=form.priority.data,
            estimated_time=estimated_time,
            project_id=project.id,
            user_id=user_id
        )
        save_to_db(task)
        
        flash(f'Tâche "{form.title.data}" créée avec succès!', 'success')
        return redirect(url_for('projects.project_details', slug_or_id=project.slug))
        
    return render_template('tasks/task_form.html', form=form, project=project, title='Nouvelle tâche')

@tasks.route('/tasks/<slug_or_id>')
@login_required
def task_details(slug_or_id):
    task = get_task_by_slug_or_id(slug_or_id)
    
    # Vérifier si le client a accès à ce projet
    if current_user.is_client():
        project = task.project
        if not current_user.has_access_to_client(project.client_id):
            flash("Vous n'avez pas accès à cette tâche.", "danger")
            return redirect(url_for('main.dashboard'))
    
    time_entries = TimeEntry.query.filter_by(task_id=task.id).order_by(TimeEntry.created_at.desc()).all()
    
    # Récupérer les commentaires liés à cette tâche
    comments = Comment.query.filter_by(task_id=task.id).order_by(Comment.created_at.desc()).all()
    
    # Formulaire pour ajouter du temps
    time_form = TimeEntryForm()
    
    # Formulaire pour ajouter un commentaire
    comment_form = CommentForm()
    
    # Formulaire pour la suppression
    delete_form = DeleteTaskForm()
    
    return render_template('tasks/task_detail.html', 
                           task=task, 
                           time_entries=time_entries,
                           comments=comments, 
                           time_form=time_form,
                           comment_form=comment_form,
                           form=delete_form,
                           title=task.title)

@tasks.route('/tasks/<slug_or_id>/edit', methods=['GET', 'POST'])
@login_and_client_required
def edit_task(slug_or_id):
    task = get_task_by_slug_or_id(slug_or_id)
    
    # Vérifier si le client a accès à ce projet
    if current_user.is_client():
        project = task.project
        if not current_user.has_access_to_client(project.client_id):
            flash("Vous n'avez pas accès à cette tâche.", "danger")
            return redirect(url_for('main.dashboard'))
    
    # Initialiser le formulaire pour tous les utilisateurs
    form = TaskForm(current_user=current_user)
    
    if form.validate_on_submit():
        user_id = form.user_id.data if form.user_id.data != 0 else None
        
        task.title = form.title.data
        task.description = form.description.data
        task.status = form.status.data
        task.priority = form.priority.data
        task.estimated_time = form.estimated_time.data
        task.user_id = user_id
        
        # Si la tâche est marquée comme terminée
        if task.status == 'terminé' and not task.completed_at:
            task.completed_at = get_utc_now()
        elif task.status != 'terminé':
            task.completed_at = None
            
        save_to_db(task)
        flash(f'Tâche "{task.title}" mise à jour!', 'success')
        return redirect(url_for('tasks.task_details', slug_or_id=task.slug))
        
    elif request.method == 'GET':
        form.title.data = task.title
        form.description.data = task.description
        form.status.data = task.status
        form.priority.data = task.priority
        form.estimated_time.data = task.estimated_time
        form.user_id.data = task.user_id if task.user_id else 0
        
    return render_template('tasks/task_form.html', form=form, task=task, title='Modifier tâche')

@tasks.route('/tasks/<slug_or_id>/clone', methods=['POST'])
@login_and_client_required
def clone_task(slug_or_id):
    """Clone une tâche existante"""
    task = get_task_by_slug_or_id(slug_or_id)
    
    # Vérifier si le client a accès à ce projet
    if current_user.is_client():
        project = task.project
        if not current_user.has_access_to_client(project.client_id):
            flash("Vous n'avez pas accès à cette tâche.", "danger")
            return redirect(url_for('main.dashboard'))
    
    # Créer une copie de la tâche
    cloned_task = task.clone()
    save_to_db(cloned_task)
    
    flash(f'Tâche "{cloned_task.title}" créée avec succès!', 'success')
    return redirect(url_for('tasks.task_details', slug_or_id=cloned_task.slug))

@tasks.route('/tasks/<slug_or_id>/delete', methods=['POST'])
@login_and_client_required
def delete_task(slug_or_id):
    task = get_task_by_slug_or_id(slug_or_id)
    project = task.project
    
    # Vérifier si le client a accès à ce projet et interdire la suppression pour les clients
    if current_user.is_client():
        flash('Accès refusé. Les clients ne peuvent pas supprimer de tâches.', 'danger')
        return redirect(url_for('tasks.task_details', slug_or_id=task.slug))
    
    # Vérifier s'il y a du temps enregistré sur cette tâche
    if task.time_entries:
        flash(f'Impossible de supprimer cette tâche car du temps y a été enregistré.', 'danger')
        return redirect(url_for('tasks.task_details', slug_or_id=task.slug))
        
    delete_from_db(task)
    flash(f'Tâche "{task.title}" supprimée!', 'success')
    return redirect(url_for('projects.project_details', slug_or_id=project.slug))

@tasks.route('/tasks/<slug_or_id>/log_time', methods=['POST'])
@login_required
def log_time(slug_or_id):
    from app.utils.email import send_task_notification
    
    task = get_task_by_slug_or_id(slug_or_id)
    
    # Vérifier si le client a accès à ce projet et interdire l'enregistrement de temps
    if current_user.is_client():
        flash('Accès refusé. Les clients ne peuvent pas enregistrer de temps.', 'danger')
        return redirect(url_for('tasks.task_details', slug_or_id=task.slug))
    
    form = TimeEntryForm()
    
    if form.validate_on_submit():
        # Vérifier s'il reste assez de crédit uniquement si la gestion de temps est activée
        if task.project.time_tracking_enabled:
            if task.project.remaining_credit < form.hours.data:
                credit_display = str(task.project.remaining_credit).replace('.', ',')
                flash(f'Pas assez de crédit restant sur le projet! ({credit_display}h disponibles)', 'danger')
                return redirect(url_for('tasks.task_details', slug_or_id=task.slug))
        
        # Créer l'entrée de temps
        time_entry = TimeEntry(
            task_id=task.id,
            user_id=current_user.id,
            hours=form.hours.data,
            description=form.description.data
        )
        db.session.add(time_entry)
        
        # Mettre à jour le temps total passé sur la tâche
        if task.actual_time is None:
            task.actual_time = form.hours.data
        else:
            task.actual_time += form.hours.data
        
        # Déduire du crédit du projet uniquement si la gestion de temps est activée
        if task.project.time_tracking_enabled:
            task.project.remaining_credit -= form.hours.data
        
        db.session.commit()
        
        # Envoyer une notification par email
        send_task_notification(task, 'time_logged', current_user, {'time_entry': time_entry})
        
        from app.utils.time_format import format_time
        flash(f'{format_time(form.hours.data)} enregistrées sur la tâche!', 'success')
        
        # Si le crédit devient faible, afficher une alerte uniquement si la gestion de temps est activée
        if task.project.time_tracking_enabled and task.project.remaining_credit < 2:
            flash(f'Attention: le crédit du projet est très bas ({format_time(task.project.remaining_credit)})!', 'warning')
            
    return redirect(url_for('tasks.task_details', slug_or_id=task.slug))

@tasks.route('/tasks/update_status', methods=['POST'])
@login_required
def update_status():
    """Route pour mettre à jour le statut d'une tâche (via drag & drop du kanban)"""
    from app.utils.email import send_task_notification
    
    data = request.get_json()
    task_id = data.get('task_id')
    new_status = data.get('status')
    
    if not task_id or not new_status:
        return jsonify({'error': 'Paramètres manquants'}), 400
        
    task = Task.query.get_or_404(task_id)
    
    # Vérifier les permissions
    if current_user.is_client():
        if not current_user.has_access_to_client(task.project.client_id):
            return jsonify({'error': 'Accès non autorisé'}), 403
    
    old_status = task.status
    task.status = new_status
    
    # Si la tâche est marquée comme terminée
    if new_status == 'terminé' and not task.completed_at:
        task.completed_at = get_utc_now()
    elif new_status != 'terminé':
        task.completed_at = None
        
    db.session.commit()
    
    # Envoyer une notification par email
    additional_data = {
        'old_status': old_status,
        'new_status': new_status
    }
    send_task_notification(task, 'status_change', current_user, additional_data)
    
    return jsonify({
        'success': True, 
        'status': new_status,
        'completed_at': task.completed_at.strftime('%d/%m/%Y') if task.completed_at else None
    })

@tasks.route('/my_tasks')
@login_required
def my_tasks():
    """Affiche les tâches assignées à l'utilisateur courant avec filtres"""
    # Récupération des paramètres de filtrage
    status = request.args.getlist('status')
    priority = request.args.get('priority')
    project_id = request.args.get('project_id', type=int)
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Construction de la requête de base
    query = Task.query.filter_by(user_id=current_user.id)

    # Filtres
    if status:
        query = query.filter(Task.status.in_(status))
    if priority:
        query = query.filter(Task.priority == priority)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if search:
        query = query.filter(Task.title.ilike(f'%{search}%'))

    # Tri par défaut : date de création décroissante
    query = query.order_by(Task.created_at.desc())

    # Récupération de toutes les tâches (sans pagination pour le tri par statut)
    all_tasks = query.all()

    # Tri des tâches par statut
    tasks_todo = [task for task in all_tasks if task.status == 'à faire']
    tasks_in_progress = [task for task in all_tasks if task.status == 'en cours']
    tasks_completed = [task for task in all_tasks if task.status == 'terminé']

    # Récupération des données pour les filtres
    projects = Project.query.all()

    # Préparation des paramètres de requête pour la pagination
    query_params = {k: v for k, v in request.args.items() if k != 'page'}

    # Déterminer si des filtres sont actifs
    filters_active = bool(status or priority or project_id or search)

    return render_template('tasks/my_tasks.html',
                         tasks_todo=tasks_todo,
                         tasks_in_progress=tasks_in_progress,
                         tasks_completed=tasks_completed,
                         projects=projects,
                         query_params=query_params,
                         filters_active=filters_active)

@tasks.route('/tasks/<slug_or_id>/add_comment', methods=['POST'])
@login_required
def add_comment(slug_or_id):
    from app.utils.email import send_task_notification
    
    task = get_task_by_slug_or_id(slug_or_id)
    
    # Vérifier si le client a accès à ce projet
    if current_user.is_client():
        project = task.project
        if not current_user.has_access_to_client(project.client_id):
            flash("Vous n'avez pas accès à cette tâche.", "danger")
            return redirect(url_for('main.dashboard'))
    
    form = CommentForm()
    
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            task_id=task.id,
            user_id=current_user.id
        )
        save_to_db(comment)
        
        # Envoyer une notification par email
        send_task_notification(task, 'comment_added', current_user, {'comment': comment})
        
        flash('Votre commentaire a été ajouté!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Erreur dans le champ {getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('tasks.task_details', slug_or_id=task.slug))

@tasks.route('/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    task = comment.task
    
    # Vérifier que l'utilisateur est l'auteur du commentaire ou un administrateur
    if comment.user_id != current_user.id and not current_user.is_admin():
        flash('Vous n\'êtes pas autorisé à supprimer ce commentaire.', 'danger')
        return redirect(url_for('tasks.task_details', slug_or_id=task.slug))
    
    delete_from_db(comment)
    flash('Commentaire supprimé avec succès!', 'success')
    return redirect(url_for('tasks.task_details', slug_or_id=task.slug))

@tasks.route('/comments/<int:comment_id>/edit', methods=['POST'])
@login_required
def edit_comment(comment_id):
    """Route pour modifier un commentaire récent (moins de 10 minutes)"""
    comment = Comment.query.get_or_404(comment_id)
    task = comment.task
    form = EditCommentForm()
    
    # Vérifier que l'utilisateur est l'auteur du commentaire
    if comment.user_id != current_user.id and not current_user.is_admin():
        flash('Vous n\'êtes pas autorisé à modifier ce commentaire.', 'danger')
        return redirect(url_for('tasks.task_details', slug_or_id=task.slug))
    
    # Vérifier que le commentaire a moins de 10 minutes
    delta = datetime.now(timezone.utc) - comment.created_at
    if delta.total_seconds() > 600:  # 10 minutes = 600 secondes
        flash('Ce commentaire ne peut plus être modifié (délai de 10 minutes dépassé).', 'warning')
        return redirect(url_for('tasks.task_details', slug_or_id=task.slug))
    
    if form.validate_on_submit():
        # Mettre à jour le commentaire
        comment.content = form.content.data
        # Pas de mise à jour de created_at pour garder l'horodatage d'origine
        save_to_db(comment)
        
        flash('Commentaire modifié avec succès !', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Erreur dans le champ {getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('tasks.task_details', slug_or_id=task.slug))