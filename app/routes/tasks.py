from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import case
from datetime import datetime, timezone
from app import db
from app.models.task import Task, TimeEntry, Comment
from app.models.project import Project
from app.models.client import Client
from app.forms.task import TaskForm, TimeEntryForm, CommentForm, EditCommentForm
from app.utils import get_utc_now
from app.utils.decorators import login_and_client_required
from app.utils.route_utils import (
    get_project_by_id, 
    get_task_by_id, 
    save_to_db, 
    delete_from_db,
    apply_filters,
    apply_sorting
)

tasks = Blueprint('tasks', __name__)

@tasks.route('/projects/<int:project_id>/tasks/new', methods=['GET', 'POST'])
@login_and_client_required
def new_task(project_id):
    project = get_project_by_id(project_id)
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
            estimated_time=estimated_time,  # Utilise None si "Non défini"
            project_id=project.id,
            user_id=user_id
        )
        save_to_db(task)
        
        flash(f'Tâche "{form.title.data}" créée avec succès!', 'success')
        return redirect(url_for('projects.project_details', project_id=project.id))
        
    return render_template('tasks/task_form.html', form=form, project=project, title='Nouvelle tâche')

@tasks.route('/tasks/<int:task_id>')
@login_required
def task_details(task_id):
    task = get_task_by_id(task_id)
    
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
    
    return render_template('tasks/task_detail.html', 
                           task=task, 
                           time_entries=time_entries,
                           comments=comments, 
                           time_form=time_form,
                           comment_form=comment_form,
                           title=task.title)

@tasks.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
@login_and_client_required
def edit_task(task_id):
    task = get_task_by_id(task_id)
    
    # Vérifier si le client a accès à ce projet
    if current_user.is_client():
        project = task.project
        if not current_user.has_access_to_client(project.client_id):
            flash("Vous n'avez pas accès à cette tâche.", "danger")
            return redirect(url_for('main.dashboard'))
    
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
        return redirect(url_for('tasks.task_details', task_id=task.id))
        
    elif request.method == 'GET':
        form.title.data = task.title
        form.description.data = task.description
        form.status.data = task.status
        form.priority.data = task.priority
        form.estimated_time.data = task.estimated_time
        form.user_id.data = task.user_id if task.user_id else 0
        
    return render_template('tasks/task_form.html', form=form, task=task, title='Modifier tâche')

@tasks.route('/tasks/<int:task_id>/delete', methods=['POST'])
@login_and_client_required
def delete_task(task_id):
    task = get_task_by_id(task_id)
    project_id = task.project_id
    
    # Vérifier si le client a accès à ce projet et interdire la suppression pour les clients
    if current_user.is_client():
        flash('Accès refusé. Les clients ne peuvent pas supprimer de tâches.', 'danger')
        return redirect(url_for('tasks.task_details', task_id=task.id))
    
    # Vérifier s'il y a du temps enregistré sur cette tâche
    if task.time_entries:
        flash(f'Impossible de supprimer cette tâche car du temps y a été enregistré.', 'danger')
        return redirect(url_for('tasks.task_details', task_id=task.id))
        
    delete_from_db(task)
    flash(f'Tâche "{task.title}" supprimée!', 'success')
    return redirect(url_for('projects.project_details', project_id=project_id))

@tasks.route('/tasks/<int:task_id>/log_time', methods=['POST'])
@login_required
def log_time(task_id):
    from app.utils.email import send_task_notification
    
    task = get_task_by_id(task_id)
    
    # Vérifier si le client a accès à ce projet et interdire l'enregistrement de temps
    if current_user.is_client():
        flash('Accès refusé. Les clients ne peuvent pas enregistrer de temps.', 'danger')
        return redirect(url_for('tasks.task_details', task_id=task.id))
    
    form = TimeEntryForm()
    
    if form.validate_on_submit():
        # Vérifier s'il reste assez de crédit
        if task.project.remaining_credit < form.hours.data:
            credit_display = str(task.project.remaining_credit).replace('.', ',')
            flash(f'Pas assez de crédit restant sur le projet! ({credit_display}h disponibles)', 'danger')
            return redirect(url_for('tasks.task_details', task_id=task.id))
        
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
        
        # Déduire du crédit du projet
        task.project.deduct_credit(form.hours.data, task.id)
        
        db.session.commit()
        
        # Envoyer une notification par email
        send_task_notification(task, 'time_logged', current_user, {'time_entry': time_entry})
        
        from app.utils.time_format import format_time
        flash(f'{format_time(form.hours.data)} enregistrées sur la tâche!', 'success')
        
        # Si le crédit devient faible, afficher une alerte
        if task.project.remaining_credit < 2:
            flash(f'Attention: le crédit du projet est très bas ({format_time(task.project.remaining_credit)})!', 'warning')
            
    return redirect(url_for('tasks.task_details', task_id=task.id))

@tasks.route('/tasks/update_status', methods=['POST'])
@login_required
def update_status():
    """Route pour mettre à jour le statut d'une tâche (via drag & drop du kanban)"""
    from app.utils.email import send_task_notification
    
    task_id = request.json.get('task_id')
    new_status = request.json.get('status')
    
    if not task_id or not new_status:
        return jsonify({'success': False, 'error': 'Données manquantes'}), 400
        
    task = get_task_by_id(task_id)
    
    # Vérifier si le client a accès à ce projet
    if current_user.is_client():
        project = task.project
        if not current_user.has_access_to_client(project.client_id):
            return jsonify({'success': False, 'error': "Vous n'avez pas accès à cette tâche."}), 403
    
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
        'message': f'Statut de la tâche "{task.title}" changé de {old_status} à {new_status}'
    })

@tasks.route('/my_tasks')
@login_required
def my_tasks():
    """Affiche les tâches assignées à l'utilisateur courant avec filtres"""
    # Récupération des paramètres de filtrage
    filters = {
        'priority': request.args.get('priority'),
        'project_id': request.args.get('project_id', type=int),
        'client_id': request.args.get('client_id', type=int),
        'search': request.args.get('search')
    }
    
    # Construction des requêtes de base pour les tâches en cours et à faire
    query_todo = Task.query.filter_by(user_id=current_user.id, status='à faire')
    query_in_progress = Task.query.filter_by(user_id=current_user.id, status='en cours')
    query_completed = Task.query.filter_by(user_id=current_user.id, status='terminé')
    
    # Si c'est un client, filtrer pour n'afficher que les tâches auxquelles il a accès
    if current_user.is_client():
        client_ids = [client.id for client in current_user.clients]
        projects = Project.query.filter(Project.client_id.in_(client_ids)).all()
        project_ids = [project.id for project in projects]
        
        query_todo = query_todo.filter(Task.project_id.in_(project_ids))
        query_in_progress = query_in_progress.filter(Task.project_id.in_(project_ids))
        query_completed = query_completed.filter(Task.project_id.in_(project_ids))
        
        # Si un client spécifique est demandé, vérifier qu'il est accessible
        if filters['client_id'] and filters['client_id'] not in client_ids:
            filters['client_id'] = None
    
    # Application des filtres
    query_todo, filters_active = apply_filters(query_todo, Task, filters)
    query_in_progress, _ = apply_filters(query_in_progress, Task, filters)
    query_completed, _ = apply_filters(query_completed, Task, filters)
    
    # Application du tri
    sort_by = request.args.get('sort_by', 'date_desc')
    if sort_by == 'priority_desc':
        # Tri par priorité (les "urgentes" en premier)
        priority_order = case(
            (Task.priority == 'urgente', 1),
            (Task.priority == 'haute', 2),
            (Task.priority == 'normale', 3),
            (Task.priority == 'basse', 4),
            else_=5
        )
        query_todo = query_todo.order_by(priority_order)
        query_in_progress = query_in_progress.order_by(priority_order)
        query_completed = query_completed.order_by(priority_order)
    elif sort_by == 'priority_asc':
        # Tri par priorité (les "basses" en premier)
        priority_order = case(
            (Task.priority == 'basse', 1),
            (Task.priority == 'normale', 2),
            (Task.priority == 'haute', 3),
            (Task.priority == 'urgente', 4),
            else_=5
        )
        query_todo = query_todo.order_by(priority_order)
        query_in_progress = query_in_progress.order_by(priority_order)
        query_completed = query_completed.order_by(priority_order)
    else:
        # Utiliser la fonction apply_sorting pour les autres cas
        query_todo = apply_sorting(query_todo, Task, sort_by.replace('_desc', ''), 'desc' if '_desc' in sort_by else 'asc')
        query_in_progress = apply_sorting(query_in_progress, Task, sort_by.replace('_desc', ''), 'desc' if '_desc' in sort_by else 'asc')
        query_completed = apply_sorting(query_completed, Task, sort_by.replace('_desc', ''), 'desc' if '_desc' in sort_by else 'asc')
    
    # Exécution des requêtes
    tasks_todo = query_todo.all()
    tasks_in_progress = query_in_progress.all()
    # Limiter les tâches terminées aux 5 plus récentes
    tasks_completed = query_completed.order_by(Task.completed_at.desc()).limit(5).all()
    
    # Récupérer tous les projets pour le filtre
    all_projects = []
    all_clients = []
    
    if current_user.is_admin() or current_user.is_technician():
        all_projects = Project.query.order_by(Project.name).all()
        all_clients = Client.query.order_by(Client.name).all()
    else:
        # Pour les clients, n'afficher que les projets auxquels ils ont accès
        all_clients = current_user.clients
        all_projects = Project.query.filter(Project.client_id.in_([c.id for c in current_user.clients])).order_by(Project.name).all()
    
    return render_template('tasks/my_tasks.html', 
                          tasks_todo=tasks_todo,
                          tasks_in_progress=tasks_in_progress,
                          tasks_completed=tasks_completed,
                          all_projects=all_projects,
                          all_clients=all_clients,
                          filters_active=filters_active,
                          title='Mes tâches')

@tasks.route('/tasks/<int:task_id>/add_comment', methods=['POST'])
@login_required
def add_comment(task_id):
    from app.utils.email import send_task_notification
    
    task = get_task_by_id(task_id)
    
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
        db.session.add(comment)
        db.session.commit()
        
        # Envoyer une notification par email
        send_task_notification(task, 'comment_added', current_user, {'comment': comment})
        
        flash('Votre commentaire a été ajouté!', 'success')
    
    return redirect(url_for('tasks.task_details', task_id=task.id))

@tasks.route('/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    delete_from_db(comment)
    task_id = comment.task_id
    
    # Vérifier que l'utilisateur est l'auteur du commentaire ou un administrateur
    if comment.user_id != current_user.id and not current_user.is_admin():
        flash('Vous n\'êtes pas autorisé à supprimer ce commentaire.', 'danger')
        return redirect(url_for('tasks.task_details', task_id=task_id))
    
    flash('Commentaire supprimé avec succès!', 'success')
    return redirect(url_for('tasks.task_details', task_id=task_id))

@tasks.route('/comments/<int:comment_id>/edit', methods=['POST'])
@login_required
def edit_comment(comment_id):
    """Route pour modifier un commentaire récent (moins de 10 minutes)"""
    comment = Comment.query.get_or_404(comment_id)
    task_id = comment.task_id
    
    # Vérifier que l'utilisateur est l'auteur du commentaire
    if comment.user_id != current_user.id and not current_user.is_admin():
        flash('Vous n\'êtes pas autorisé à modifier ce commentaire.', 'danger')
        return redirect(url_for('tasks.task_details', task_id=task_id))
    
    # Vérifier que le commentaire a moins de 10 minutes
    delta = datetime.now(timezone.utc) - comment.created_at
    if delta.total_seconds() > 600:  # 10 minutes = 600 secondes
        flash('Ce commentaire ne peut plus être modifié (délai de 10 minutes dépassé).', 'warning')
        return redirect(url_for('tasks.task_details', task_id=task_id))
    
    form = EditCommentForm()
    if form.validate_on_submit():
        # Mettre à jour le commentaire
        comment.content = form.content.data
        # Pas de mise à jour de created_at pour garder l'horodatage d'origine
        db.session.commit()
        
        flash('Commentaire modifié avec succès !', 'success')
    else:
        flash('Erreur lors de la modification du commentaire.', 'danger')
    
    return redirect(url_for('tasks.task_details', task_id=task_id))