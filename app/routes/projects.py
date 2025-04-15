from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.models.project import Project, CreditLog
from app.models.client import Client
from app.forms.project import ProjectForm, AddCreditForm

projects = Blueprint('projects', __name__)

@projects.route('/projects')
@login_required
def list_projects():
    all_projects = Project.query.order_by(Project.created_at.desc()).all()
    # Calculer le pourcentage de crédit restant pour chaque projet
    for project in all_projects:
        if project.initial_credit > 0:
            project.credit_percent = (project.remaining_credit / project.initial_credit) * 100
        else:
            project.credit_percent = 0
            
    return render_template('projects/projects.html', projects=all_projects, title='Projets')

@projects.route('/clients/<int:client_id>/projects/new', methods=['GET', 'POST'])
@login_required
def new_project(client_id):
    client = Client.query.get_or_404(client_id)
    form = ProjectForm()
    
    if form.validate_on_submit():
        # Créer le projet sans appeler add_credit
        project = Project(
            name=form.name.data,
            description=form.description.data,
            initial_credit=form.initial_credit.data,
            remaining_credit=form.initial_credit.data,
            client_id=client.id
        )
        
        # Ajouter et commit pour obtenir l'ID
        db.session.add(project)
        db.session.commit()
        
        # Maintenant, créer manuellement l'entrée de log
        credit_log = CreditLog(
            project_id=project.id,  # Maintenant project.id devrait être défini
            amount=form.initial_credit.data,
            note="Crédit initial"
        )
        db.session.add(credit_log)
        
        # Commit à nouveau pour sauvegarder le log
        db.session.commit()
        
        flash(f'Projet {form.name.data} créé avec succès!', 'success')
        return redirect(url_for('clients.client_details', client_id=client.id))
        
    return render_template('projects/project_form.html', form=form, client=client, title='Nouveau projet')

@projects.route('/projects/<int:project_id>')
@login_required
def project_details(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Calculer le pourcentage de crédit restant
    if project.initial_credit > 0:
        project.credit_percent = (project.remaining_credit / project.initial_credit) * 100
    else:
        project.credit_percent = 0
        
    # Récupérer l'historique des crédits
    credit_logs = project.credit_logs
    
    # Récupérer les tâches organisées par statut pour le kanban
    tasks_todo = [t for t in project.tasks if t.status == 'à faire']
    tasks_in_progress = [t for t in project.tasks if t.status == 'en cours']
    tasks_done = [t for t in project.tasks if t.status == 'terminé']
    
    return render_template('projects/project_detail.html', 
                           project=project, 
                           credit_logs=credit_logs,
                           tasks_todo=tasks_todo,
                           tasks_in_progress=tasks_in_progress,
                           tasks_done=tasks_done,
                           title=project.name)

@projects.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    form = ProjectForm()
    
    if form.validate_on_submit():
        # Si le crédit initial a changé, ajuster le crédit restant
        credit_diff = form.initial_credit.data - project.initial_credit
        
        project.name = form.name.data
        project.description = form.description.data
        project.initial_credit = form.initial_credit.data
        
        if credit_diff != 0:
            project.remaining_credit += credit_diff
            project.add_credit(credit_diff, "Ajustement du crédit initial")
        
        db.session.commit()
        flash(f'Projet {project.name} mis à jour avec succès!', 'success')
        return redirect(url_for('projects.project_details', project_id=project.id))
        
    elif request.method == 'GET':
        form.name.data = project.name
        form.description.data = project.description
        form.initial_credit.data = project.initial_credit
        
    return render_template('projects/project_form.html', form=form, project=project, title='Modifier projet')

@projects.route('/projects/<int:project_id>/add_credit', methods=['GET', 'POST'])
@login_required
def add_credit(project_id):
    project = Project.query.get_or_404(project_id)
    form = AddCreditForm()
    
    if form.validate_on_submit():
        project.add_credit(form.amount.data, form.note.data)
        db.session.commit()
        flash(f'{form.amount.data}h ajoutées au crédit du projet {project.name}!', 'success')
        return redirect(url_for('projects.project_details', project_id=project.id))
        
    return render_template('projects/add_credit.html', form=form, project=project, title='Ajouter du crédit')

@projects.route('/projects/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    client_id = project.client_id
    
    # Vérifier s'il y a des tâches liées
    if project.tasks:
        flash(f'Impossible de supprimer le projet {project.name} car des tâches lui sont associées.', 'danger')
        return redirect(url_for('projects.project_details', project_id=project.id))
        
    db.session.delete(project)
    db.session.commit()
    flash(f'Projet {project.name} supprimé avec succès!', 'success')
    return redirect(url_for('clients.client_details', client_id=client_id))