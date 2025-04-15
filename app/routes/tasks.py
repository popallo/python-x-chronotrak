from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models.task import Task, TimeEntry
from app.models.project import Project
from app.forms.task import TaskForm, TimeEntryForm

tasks = Blueprint('tasks', __name__)

@tasks.route('/projects/<int:project_id>/tasks/new', methods=['GET', 'POST'])
@login_required
def new_task(project_id):
    project = Project.query.get_or_404(project_id)
    form = TaskForm()
    
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
    time_entries = TimeEntry.query.filter_by(task_id=task.id).order_by(TimeEntry.created_at.desc()).all()
    
    # Formulaire pour ajouter du temps
    time_form = TimeEntryForm()
    
    return render_template('tasks/task_detail.html', 
                           task=task, 
                           time_entries=time_entries, 
                           time_form=time_form,
                           title=task.title)

@tasks.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    form = TaskForm()
    
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
            task.completed_at = datetime.utcnow()
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
    task = Task.query.get_or_404(task_id)
    form = TimeEntryForm()
    
    if form.validate_on_submit():
        # Vérifier s'il reste assez de crédit
        if task.project.remaining_credit < form.hours.data:
            flash(f'Pas assez de crédit restant sur le projet! ({task.project.remaining_credit}h disponibles)', 'danger')
            return redirect(url_for('tasks.task_details', task_id=task.id))
            
        # Enregistrer le temps
        task.log_time(
            hours=form.hours.data,
            user_id=current_user.id,
            description=form.description.data
        )
        
        db.session.commit()
        flash(f'{form.hours.data}h enregistrées sur la tâche!', 'success')
        
        # Si le crédit devient faible, afficher une alerte
        if task.project.remaining_credit < 2:
            flash(f'Attention: le crédit du projet est très bas ({task.project.remaining_credit}h)!', 'warning')
            
    return redirect(url_for('tasks.task_details', task_id=task.id))

@tasks.route('/tasks/update_status', methods=['POST'])
@login_required
def update_status():
    """Route pour mettre à jour le statut d'une tâche (via drag & drop du kanban)"""
    task_id = request.json.get('task_id')
    new_status = request.json.get('status')
    
    if not task_id or not new_status:
        return jsonify({'success': False, 'error': 'Données manquantes'}), 400
        
    task = Task.query.get_or_404(task_id)
    old_status = task.status
    task.status = new_status
    
    # Si la tâche est marquée comme terminée
    if new_status == 'terminé' and not task.completed_at:
        task.completed_at = datetime.utcnow()
    elif new_status != 'terminé':
        task.completed_at = None
        
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': f'Statut de la tâche "{task.title}" changé de {old_status} à {new_status}'
    })

@tasks.route('/my_tasks')
@login_required
def my_tasks():
    """Affiche les tâches assignées à l'utilisateur courant"""
    tasks_todo = Task.query.filter_by(user_id=current_user.id, status='à faire').all()
    tasks_in_progress = Task.query.filter_by(user_id=current_user.id, status='en cours').all()
    
    return render_template('tasks/my_tasks.html', 
                          tasks_todo=tasks_todo,
                          tasks_in_progress=tasks_in_progress,
                          title='Mes tâches')