from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models.task import Task, TimeEntry, Comment
from app.models.project import Project
from app.models.client import Client
from app.forms.task import TaskForm, TimeEntryForm, CommentForm
from app.utils import get_utc_now
from app.utils.decorators import client_required

tasks = Blueprint('tasks', __name__)

@tasks.route('/projects/<int:project_id>/tasks/new', methods=['GET', 'POST'])
@login_required
@client_required
def new_task(project_id):
    project = Project.query.get_or_404(project_id)
    form = TaskForm(current_user=current_user)
    
    if form.validate_on_submit():
        user_id = form.user_id.data if form.user_id.data != 0 else None
        
        task = Task(
            title=form.title.data,
            description=form.description.data,
            status=form.status.data,
            priority=form.priority.data,
            estimated_time=form.estimated_time.data,
            project_id=project.id,
            user_id=user_id
        )
        db.session.add(task)
        db.session.commit()
        
        flash(f'Tâche "{form.title.data}" créée avec succès!', 'success')
        return redirect(url_for('projects.project_details', project_id=project.id))
        
    return render_template('tasks/task_form.html', form=form, project=project, title='Nouvelle tâche')

@tasks.route('/tasks/<int:task_id>')
@login_required
def task_details(task_id):
    task = Task.query.get_or_404(task_id)
    
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
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    
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
            
        db.session.commit()
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
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    project_id = task.project_id
    
    # Vérifier si le client a accès à ce projet et interdire la suppression pour les clients
    if current_user.is_client():
        flash('Accès refusé. Les clients ne peuvent pas supprimer de tâches.', 'danger')
        return redirect(url_for('tasks.task_details', task_id=task.id))
    
    # Vérifier s'il y a du temps enregistré sur cette tâche
    if task.time_entries:
        flash(f'Impossible de supprimer cette tâche car du temps y a été enregistré.', 'danger')
        return redirect(url_for('tasks.task_details', task_id=task.id))
        
    db.session.delete(task)
    db.session.commit()
    flash(f'Tâche "{task.title}" supprimée!', 'success')
    return redirect(url_for('projects.project_details', project_id=project_id))

@tasks.route('/tasks/<int:task_id>/log_time', methods=['POST'])
@login_required
def log_time(task_id):
    from app.utils.email import send_task_notification
    
    task = Task.query.get_or_404(task_id)
    
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
        
        flash(f'{form.hours.data}h enregistrées sur la tâche!', 'success')
        
        # Si le crédit devient faible, afficher une alerte
        if task.project.remaining_credit < 2:
            flash(f'Attention: le crédit du projet est très bas ({task.project.remaining_credit}h)!', 'warning')
            
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
        
    task = Task.query.get_or_404(task_id)
    
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
    priority = request.args.get('priority')
    project_id = request.args.get('project_id', type=int)
    client_id = request.args.get('client_id', type=int)
    search = request.args.get('search')
    sort_by = request.args.get('sort_by', 'date_desc')
    
    # Construction des requêtes de base pour les tâches en cours et à faire
    query_todo = Task.query.filter_by(user_id=current_user.id, status='à faire')
    query_in_progress = Task.query.filter_by(user_id=current_user.id, status='en cours')
    query_completed = Task.query.filter_by(user_id=current_user.id, status='terminé')
    
    # Flag pour savoir si des filtres sont actifs
    filters_active = bool(priority or project_id or client_id or search)
    
    # Si c'est un client, filtrer pour n'afficher que les tâches auxquelles il a accès
    if current_user.is_client():
        client_ids = [client.id for client in current_user.clients]
        projects = Project.query.filter(Project.client_id.in_(client_ids)).all()
        project_ids = [project.id for project in projects]
        
        query_todo = query_todo.filter(Task.project_id.in_(project_ids))
        query_in_progress = query_in_progress.filter(Task.project_id.in_(project_ids))
        query_completed = query_completed.filter(Task.project_id.in_(project_ids))
        
        # Si un client spécifique est demandé, vérifier qu'il est accessible
        if client_id and client_id not in client_ids:
            # Si le client demandé n'est pas accessible, ignorer ce filtre
            client_id = None
    
    # Application des filtres
    if priority:
        query_todo = query_todo.filter(Task.priority == priority)
        query_in_progress = query_in_progress.filter(Task.priority == priority)
        query_completed = query_completed.filter(Task.priority == priority)
    
    if project_id:
        query_todo = query_todo.filter(Task.project_id == project_id)
        query_in_progress = query_in_progress.filter(Task.project_id == project_id)
        query_completed = query_completed.filter(Task.project_id == project_id)
    
    if client_id:
        # Trouver d'abord les projets liés à ce client
        projects_for_client = Project.query.filter_by(client_id=client_id).all()
        project_ids_for_client = [p.id for p in projects_for_client]
        
        query_todo = query_todo.filter(Task.project_id.in_(project_ids_for_client))
        query_in_progress = query_in_progress.filter(Task.project_id.in_(project_ids_for_client))
        query_completed = query_completed.filter(Task.project_id.in_(project_ids_for_client))
    
    if search:
        search_term = f"%{search}%"
        query_todo = query_todo.filter(Task.title.ilike(search_term))
        query_in_progress = query_in_progress.filter(Task.title.ilike(search_term))
        query_completed = query_completed.filter(Task.title.ilike(search_term))
    
    # Application du tri
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
    elif sort_by == 'date_asc':
        query_todo = query_todo.order_by(Task.created_at.asc())
        query_in_progress = query_in_progress.order_by(Task.created_at.asc())
        query_completed = query_completed.order_by(Task.created_at.asc())
    elif sort_by == 'date_desc':
        query_todo = query_todo.order_by(Task.created_at.desc())
        query_in_progress = query_in_progress.order_by(Task.created_at.desc())
        query_completed = query_completed.order_by(Task.completed_at.desc())
    elif sort_by == 'title':
        query_todo = query_todo.order_by(Task.title.asc())
        query_in_progress = query_in_progress.order_by(Task.title.asc())
        query_completed = query_completed.order_by(Task.title.asc())
    
    # Exécution des requêtes
    tasks_todo = query_todo.all()
    tasks_in_progress = query_in_progress.all()
    # Limiter les tâches terminées aux 5 plus récentes
    tasks_completed = query_completed.limit(5).all()
    
    # Récupérer tous les projets pour le filtre
    all_projects = []
    all_clients = []
    
    if current_user.is_admin() or current_user.is_technician():
        all_projects = Project.query.order_by(Project.name).all()
        all_clients = Client.query.order_by(Client.name).all()
    else:
        # Pour les clients, n'afficher que les projets auxquels ils ont accès
        client_ids = [client.id for client in current_user.clients]
        all_clients = current_user.clients
        all_projects = Project.query.filter(Project.client_id.in_(client_ids)).order_by(Project.name).all()
    
    # Helper functions pour le template
    def get_project_by_id(project_id):
        return Project.query.get(project_id)
        
    def get_client_by_id(client_id):
        return Client.query.get(client_id)
    
    return render_template('tasks/my_tasks.html', 
                          tasks_todo=tasks_todo,
                          tasks_in_progress=tasks_in_progress,
                          tasks_completed=tasks_completed,
                          all_projects=all_projects,
                          all_clients=all_clients,
                          filters_active=filters_active,
                          get_project_by_id=get_project_by_id,
                          get_client_by_id=get_client_by_id,
                          title='Mes tâches')

@tasks.route('/tasks/<int:task_id>/add_comment', methods=['POST'])
@login_required
def add_comment(task_id):
    from app.utils.email import send_task_notification
    
    task = Task.query.get_or_404(task_id)
    
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
    task_id = comment.task_id
    
    # Vérifier que l'utilisateur est l'auteur du commentaire ou un administrateur
    if comment.user_id != current_user.id and not current_user.is_admin():
        flash('Vous n\'êtes pas autorisé à supprimer ce commentaire.', 'danger')
        return redirect(url_for('tasks.task_details', task_id=task_id))
    
    db.session.delete(comment)
    db.session.commit()
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
    delta = datetime.now(datetime.timezone.utc) - comment.created_at
    if delta.total_seconds() > 600:  # 10 minutes = 600 secondes
        flash('Ce commentaire ne peut plus être modifié (délai de 10 minutes dépassé).', 'warning')
        return redirect(url_for('tasks.task_details', task_id=task_id))
    
    # Récupérer le nouveau contenu
    new_content = request.form.get('content')
    if not new_content or new_content.strip() == '':
        flash('Le commentaire ne peut pas être vide.', 'danger')
        return redirect(url_for('tasks.task_details', task_id=task_id))
    
    # Mettre à jour le commentaire
    comment.content = new_content
    # Pas de mise à jour de created_at pour garder l'horodatage d'origine
    db.session.commit()
    
    flash('Commentaire modifié avec succès !', 'success')
    return redirect(url_for('tasks.task_details', task_id=task_id))