from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import case
from datetime import datetime, timezone
from app import db
from app.models.task import Task, TimeEntry, Comment, ChecklistItem, UserPinnedTask
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
import json

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
    form = TaskForm(current_user=current_user, project=project)
    
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
    
    # Récupérer les commentaires liés à cette tâche (sans les réponses)
    comments = Comment.query.filter_by(task_id=task.id, parent_id=None).order_by(Comment.created_at.desc()).all()
    
    # Formulaire pour ajouter du temps
    time_form = TimeEntryForm()
    
    # Formulaire pour ajouter un commentaire
    comment_form = CommentForm()
    
    # Formulaire pour éditer un commentaire
    edit_comment_form = EditCommentForm()
    
    # Formulaire pour la suppression
    delete_form = DeleteTaskForm()
    
    return render_template('tasks/task_detail.html', 
                           task=task, 
                           time_entries=time_entries,
                           comments=comments, 
                           time_form=time_form,
                           comment_form=comment_form,
                           edit_comment_form=edit_comment_form,
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
    form = TaskForm(current_user=current_user, project=task.project)
    
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
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Accès refusé. Les clients ne peuvent pas enregistrer de temps.'}), 403
        flash('Accès refusé. Les clients ne peuvent pas enregistrer de temps.', 'danger')
        return redirect(url_for('tasks.task_details', slug_or_id=task.slug))
    
    form = TimeEntryForm()
    
    if form.validate_on_submit():
        # Convertir le temps en minutes
        time_in_minutes = int(form.hours.data * 60)
        
        # Vérifier s'il reste assez de crédit uniquement si la gestion de temps est activée
        if task.project.time_tracking_enabled:
            # Si remaining_credit est inférieur à 100, on considère que c'est en heures
            current_credit = task.project.remaining_credit
            if current_credit < 100:  # Probablement en heures
                current_credit = current_credit * 60  # Convertir en minutes
            
            if current_credit < time_in_minutes:
                # Formater le temps restant en heures et minutes
                remaining_hours = current_credit // 60
                remaining_minutes = current_credit % 60
                if remaining_hours > 0:
                    credit_display = f"{remaining_hours}h{remaining_minutes:02d}min"
                else:
                    credit_display = f"{remaining_minutes}min"
                
                if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False, 
                        'error': f'Pas assez de crédit restant sur le projet! ({credit_display} disponibles)'
                    }), 400
                flash(f'Pas assez de crédit restant sur le projet! ({credit_display} disponibles)', 'danger')
                return redirect(url_for('tasks.task_details', slug_or_id=task.slug))
        
        # Créer l'entrée de temps
        time_entry = TimeEntry(
            task_id=task.id,
            user_id=current_user.id,
            minutes=time_in_minutes,
            description=form.description.data
        )
        db.session.add(time_entry)
        
        # Mettre à jour le temps total passé sur la tâche
        if task.actual_minutes is None:
            task.actual_minutes = time_in_minutes
        else:
            task.actual_minutes += time_in_minutes
        
        # Déduire du crédit du projet uniquement si la gestion de temps est activée
        if task.project.time_tracking_enabled:
            # Le crédit est toujours stocké en minutes dans la base de données
            task.project.remaining_credit -= time_in_minutes
        
        db.session.commit()
        
        # Envoyer une notification par email
        send_task_notification(task, 'time_logged', current_user, {'time_entry': time_entry}, notify_all=True)
        
        # Formater le temps enregistré en heures et minutes
        hours = time_in_minutes // 60
        minutes = time_in_minutes % 60
        if hours > 0:
            time_display = f"{hours}h{minutes:02d}min"
        else:
            time_display = f"{minutes}min"
        success_message = f'{time_display} enregistrées sur la tâche!'
        
        # Si le crédit devient faible, afficher une alerte uniquement si la gestion de temps est activée
        warning_message = None
        if task.project.time_tracking_enabled:
            current_credit = task.project.remaining_credit
            if current_credit < 120:  # 2 heures en minutes
                remaining_hours = current_credit // 60
                remaining_minutes = current_credit % 60
                if remaining_hours > 0:
                    credit_display = f"{remaining_hours}h{remaining_minutes:02d}min"
                else:
                    credit_display = f"{remaining_minutes}min"
                warning_message = f'Attention: le crédit du projet est très bas ({credit_display})!'
        
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Formater le temps restant pour l'affichage
            remaining_hours = task.project.remaining_credit // 60
            remaining_minutes = task.project.remaining_credit % 60
            if remaining_hours > 0:
                remaining_display = f"{remaining_hours}h{remaining_minutes:02d}min"
            else:
                remaining_display = f"{remaining_minutes}min"
                
            return jsonify({
                'success': True,
                'message': success_message,
                'warning': warning_message,
                'time_entry': {
                    'id': time_entry.id,
                    'hours': time_entry.minutes / 60,  # Garder en décimal pour le calcul
                    'description': time_entry.description,
                    'created_at': time_entry.created_at.strftime('%d/%m %H:%M'),
                    'user_name': time_entry.user.name
                },
                'task': {
                    'actual_time': task.actual_minutes / 60 if task.actual_minutes else None,  # Garder en décimal pour le calcul
                    'remaining_credit': remaining_display if task.project.time_tracking_enabled else None  # Afficher en format humain
                }
            })
            
        flash(success_message, 'success')
        if warning_message:
            flash(warning_message, 'warning')
            
    return redirect(url_for('tasks.task_details', slug_or_id=task.slug))

@tasks.route('/tasks/<slug_or_id>/time_entries', methods=['GET'])
@login_required
def get_time_entries(slug_or_id):
    task = get_task_by_slug_or_id(slug_or_id)
    time_entries = TimeEntry.query.filter_by(task_id=task.id).order_by(TimeEntry.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'time_entries': [{
            'id': entry.id,
            'hours': entry.minutes / 60,  # Convertir les minutes en heures pour l'affichage
            'description': entry.description,
            'created_at': entry.created_at.strftime('%d/%m %H:%M'),
            'user_name': entry.user.name
        } for entry in time_entries],
        'task': {
            'actual_time': task.actual_minutes / 60 if task.actual_minutes else None,  # Convertir en heures
            'remaining_credit': task.project.remaining_credit / 60 if task.project.time_tracking_enabled else None  # Convertir en heures
        }
    })

@tasks.route('/tasks/update_status', methods=['POST'])
@login_required
def update_status():
    """Route pour mettre à jour le statut d'une tâche (via drag & drop du kanban)"""
    from app.utils.email import send_task_notification
    
    try:
        data = request.get_json()
        current_app.logger.info(f"Données reçues: {data}")
        
        task_id = data.get('task_id')
        new_status = data.get('status')
        
        if not task_id or not new_status:
            current_app.logger.error(f"Paramètres manquants: task_id={task_id}, status={new_status}")
            return jsonify({'success': False, 'error': 'Paramètres manquants'}), 400
            
        task = Task.query.get_or_404(task_id)
        
        # Vérifier les permissions
        if current_user.is_client():
            if not current_user.has_access_to_client(task.project.client_id):
                current_app.logger.error(f"Accès non autorisé pour l'utilisateur {current_user.id} à la tâche {task_id}")
                return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403
        
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
        send_task_notification(
            task=task,
            event_type='status_change',
            user=current_user,
            additional_data=additional_data,
            notify_all=True  # Activer les notifications pour tous les participants
        )
        
        current_app.logger.info(f"Statut de la tâche {task_id} mis à jour de '{old_status}' à '{new_status}'")
        
        return jsonify({
            'success': True, 
            'status': new_status,
            'completed_at': task.completed_at.strftime('%d/%m/%Y') if task.completed_at else None
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la mise à jour du statut: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

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
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': "Vous n'avez pas accès à cette tâche."}), 403
            flash("Vous n'avez pas accès à cette tâche.", "danger")
            return redirect(url_for('main.dashboard'))
    
    form = CommentForm()
    
    if form.validate_on_submit():
        # Récupérer les mentions depuis le champ caché
        mentioned_users = []
        try:
            mentions_data = request.form.get('mentions', '[]')
            mentioned_users = json.loads(mentions_data)
        except json.JSONDecodeError:
            current_app.logger.warning("Erreur lors du décodage des mentions")
        
        comment = Comment(
            content=form.content.data,
            task_id=task.id,
            user_id=current_user.id
        )
        save_to_db(comment)
        
        # Envoyer une notification en fonction des paramètres
        send_task_notification(
            task=task,
            event_type='comment_added',
            user=current_user,
            additional_data={'comment': comment},
            notify_all=form.notify_all.data,
            mentioned_users=mentioned_users
        )
        
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': 'Votre commentaire a été ajouté.',
                'comment': {
                    'id': comment.id,
                    'content': comment.content,
                    'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M'),
                    'user_name': comment.user.name,
                    'user_id': comment.user.id,
                    'is_own_comment': comment.user_id == current_user.id
                }
            })
            
        flash('Votre commentaire a été ajouté.', 'success')
        return redirect(url_for('tasks.task_details', slug_or_id=slug_or_id))
    
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        errors = {}
        for field, field_errors in form.errors.items():
            errors[field] = field_errors[0]
        return jsonify({
            'success': False,
            'errors': errors
        }), 400
    
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'Erreur dans le champ {getattr(form, field).label.text} : {error}', 'danger')
    
    return redirect(url_for('tasks.task_details', slug_or_id=slug_or_id))

@tasks.route('/tasks/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    task = comment.task
    
    # Vérifier que l'utilisateur est l'auteur du commentaire ou un administrateur
    if comment.user_id != current_user.id and not current_user.is_admin():
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Vous n\'êtes pas autorisé à supprimer ce commentaire.'}), 403
        flash('Vous n\'êtes pas autorisé à supprimer ce commentaire.', 'danger')
        return redirect(url_for('tasks.task_details', slug_or_id=task.slug))
    
    delete_from_db(comment)
    
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': 'Commentaire supprimé avec succès!'
        })
        
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
    now = datetime.now(timezone.utc)
    comment_time = comment.created_at.replace(tzinfo=timezone.utc) if comment.created_at.tzinfo is None else comment.created_at
    delta = now - comment_time
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

@tasks.route('/tasks/<slug_or_id>/checklist', methods=['POST'])
@login_required
def add_checklist_item(slug_or_id):
    task = get_task_by_slug_or_id(slug_or_id)
    
    # Vérifier si le client a accès à ce projet
    if current_user.is_client():
        if not current_user.has_access_to_client(task.project.client_id):
            return jsonify({'error': 'Accès non autorisé'}), 403
    
    data = request.get_json()
    
    if not data or 'content' not in data:
        return jsonify({'error': 'Contenu manquant'}), 400
    
    # Vérifier si c'est un shortcode
    if data.get('is_shortcode', False):
        if task.parse_checklist_shortcode(data['content']):
            return jsonify({'success': True, 'message': 'Checklist créée avec succès'}), 201
        else:
            return jsonify({'error': 'Format de shortcode invalide'}), 400
    
    # Sinon, ajouter un élément normal
    item = task.add_checklist_item(data['content'])
    
    return jsonify({
        'success': True,
        'item': {
            'id': item.id,
            'content': item.content,
            'is_checked': item.is_checked,
            'position': item.position
        }
    }), 201

@tasks.route('/tasks/<slug_or_id>/checklist/<int:item_id>', methods=['PUT'])
@login_required
def update_checklist_item(slug_or_id, item_id):
    task = get_task_by_slug_or_id(slug_or_id)
    
    # Vérifier si le client a accès à ce projet
    if current_user.is_client():
        if not current_user.has_access_to_client(task.project.client_id):
            return jsonify({'error': 'Accès non autorisé'}), 403
    
    item = ChecklistItem.query.get_or_404(item_id)
    
    # Vérifier que l'élément appartient bien à la tâche
    if item.task_id != task.id:
        return jsonify({'error': 'Élément non trouvé dans cette tâche'}), 404
    
    data = request.get_json()
    
    if 'is_checked' in data:
        item.is_checked = data['is_checked']
    
    if 'content' in data:
        item.content = data['content']
    
    if 'position' in data:
        item.position = data['position']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'item': {
            'id': item.id,
            'content': item.content,
            'is_checked': item.is_checked,
            'position': item.position
        }
    })

@tasks.route('/tasks/<slug_or_id>/checklist/<int:item_id>', methods=['DELETE'])
@login_required
def delete_checklist_item(slug_or_id, item_id):
    task = get_task_by_slug_or_id(slug_or_id)
    
    # Vérifier si le client a accès à ce projet
    if current_user.is_client():
        if not current_user.has_access_to_client(task.project.client_id):
            return jsonify({'error': 'Accès non autorisé'}), 403
    
    item = ChecklistItem.query.get_or_404(item_id)
    
    # Vérifier que l'élément appartient bien à la tâche
    if item.task_id != task.id:
        return jsonify({'error': 'Élément non trouvé dans cette tâche'}), 404
    
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({'success': True})

@tasks.route('/tasks/<slug_or_id>/checklist/reorder', methods=['POST'])
@login_required
def reorder_checklist(slug_or_id):
    task = get_task_by_slug_or_id(slug_or_id)
    
    # Vérifier si le client a accès à ce projet
    if current_user.is_client():
        if not current_user.has_access_to_client(task.project.client_id):
            return jsonify({'error': 'Accès non autorisé'}), 403
    
    data = request.get_json()
    
    if not data or 'items' not in data:
        return jsonify({'error': 'Données manquantes'}), 400
    
    # Mettre à jour les positions
    for item_data in data['items']:
        item = ChecklistItem.query.get(item_data['id'])
        if item and item.task_id == task.id:
            item.position = item_data['position']
    
    db.session.commit()
    
    return jsonify({'success': True})

@tasks.route('/comments/<int:comment_id>/reply', methods=['POST'])
@login_required
def add_reply(comment_id):
    """Ajoute une réponse à un commentaire"""
    parent_comment = Comment.query.get_or_404(comment_id)
    task = parent_comment.task
    
    # Vérifier si le client a accès à ce projet
    if current_user.is_client():
        if not current_user.has_access_to_client(task.project.client_id):
            if request.is_json:
                return jsonify({'success': False, 'error': "Vous n'avez pas accès à cette tâche."}), 403
            flash("Vous n'avez pas accès à cette tâche.", "danger")
            return redirect(url_for('main.dashboard'))
    
    form = CommentForm()
    
    if form.validate_on_submit():
        reply = Comment(
            content=form.content.data,
            task_id=task.id,
            user_id=current_user.id,
            parent_id=parent_comment.id
        )
        save_to_db(reply)
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Réponse ajoutée avec succès!',
                'comment': {
                    'id': reply.id,
                    'content': reply.content,
                    'created_at': reply.created_at.strftime('%d/%m/%Y %H:%M'),
                    'user_name': reply.user.name,
                    'user_id': reply.user.id,
                    'is_own_comment': reply.user_id == current_user.id,
                    'parent_id': reply.parent_id
                }
            })
            
        flash('Réponse ajoutée avec succès!', 'success')
    else:
        if request.is_json:
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = field_errors[0]
            return jsonify({
                'success': False,
                'errors': errors
            }), 400
            
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Erreur dans le champ {getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('tasks.task_details', slug_or_id=task.slug))

@tasks.route('/task/<slug_or_id>/toggle_pin', methods=['POST'])
@login_required
def toggle_pin_task(slug_or_id):
    """Épingler ou désépingler une tâche pour l'utilisateur courant"""
    try:
        task = get_task_by_slug_or_id(slug_or_id)
        if not task:
            if request.is_json:
                return jsonify({'error': 'Tâche non trouvée.'}), 404
            flash('Tâche non trouvée.', 'danger')
            return redirect(url_for('main.dashboard'))

        # Vérifier les permissions
        if current_user.is_client() and task.project.client not in current_user.clients:
            if request.is_json:
                return jsonify({'error': 'Vous n\'avez pas la permission d\'effectuer cette action.'}), 403
            flash('Vous n\'avez pas la permission d\'effectuer cette action.', 'danger')
            return redirect(url_for('main.dashboard'))

        # Vérifier si la tâche est déjà épinglée
        is_pinned = task in current_user.pinned_tasks
        if is_pinned:
            # Désépingler
            UserPinnedTask.query.filter_by(user_id=current_user.id, task_id=task.id).delete()
            db.session.commit()
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'La tâche a été désépinglée.',
                    'is_pinned': False,
                    'task_id': task.id
                })
            flash('La tâche a été désépinglée.', 'success')
        else:
            # Épingler
            new_pin = UserPinnedTask(user_id=current_user.id, task_id=task.id)
            db.session.add(new_pin)
            db.session.commit()
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'La tâche a été épinglée.',
                    'is_pinned': True,
                    'task_id': task.id
                })
            flash('La tâche a été épinglée.', 'success')

        if request.is_json:
            return jsonify({'success': True})
        return redirect(request.referrer or url_for('tasks.task_details', slug_or_id=task.slug))
    except Exception as e:
        db.session.rollback()  # Annuler toute transaction en cours
        if request.is_json:
            return jsonify({
                'error': 'Une erreur est survenue lors de l\'opération.',
                'details': str(e)
            }), 500
        flash('Une erreur est survenue lors de l\'opération.', 'danger')
        return redirect(request.referrer or url_for('main.dashboard'))

@tasks.route('/api/tasks/<slug_or_id>/remaining-credit', methods=['GET'])
@login_required
def get_remaining_credit(slug_or_id):
    """Récupère le crédit restant d'une tâche"""
    task = get_task_by_slug_or_id(slug_or_id)
    
    # Vérifier si le client a accès à ce projet
    if current_user.is_client():
        project = task.project
        if not current_user.has_access_to_client(project.client_id):
            return jsonify({'error': 'Accès non autorisé'}), 403
    
    # Le crédit est toujours stocké en minutes dans la base de données
    remaining_credit = task.project.remaining_credit
    if task.project.time_tracking_enabled and remaining_credit is not None:
        # Convertir en heures pour l'affichage
        remaining_credit = remaining_credit / 60
    
    return jsonify({
        'success': True,
        'remaining_credit': remaining_credit
    })