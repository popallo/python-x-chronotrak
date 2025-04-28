from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.project import Project, CreditLog
from app.models.client import Client
from app.forms.project import ProjectForm, AddCreditForm
from app.utils.decorators import client_required
from datetime import datetime
from sqlalchemy import or_, and_, func

projects = Blueprint('projects', __name__)

@projects.route('/projects')
@login_required
def list_projects():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Nombre de projets par page
    
    # Construire la requête de base en fonction du rôle de l'utilisateur
    if current_user.is_admin() or current_user.is_technician():
        query = Project.query
    else:
        # Pour les clients, montrer uniquement les projets des clients associés
        client_ids = [client.id for client in current_user.clients]
        query = Project.query.filter(Project.client_id.in_(client_ids))
    
    # Appliquer les filtres de la requête
    filters_active = False  # Flag pour savoir si des filtres sont actifs
    
    # Filtre par client
    client_id = request.args.get('client_id', type=int)
    if client_id:
        query = query.filter(Project.client_id == client_id)
        filters_active = True
    
    # Filtre par état de crédit
    credit_status = request.args.get('credit_status')
    if credit_status:
        filters_active = True
        if credit_status == 'critical':
            query = query.filter(Project.remaining_credit < 2)
        elif credit_status == 'low':
            query = query.filter(Project.remaining_credit < 5, Project.remaining_credit >= 2)
        elif credit_status == 'normal':
            query = query.filter(Project.remaining_credit >= 5)
    
    # Recherche par nom
    search = request.args.get('search')
    if search:
        query = query.filter(Project.name.ilike(f'%{search}%'))
        filters_active = True
    
    # Filtre par période de création
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Project.created_at >= date_from)
            filters_active = True
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            # Ajouter 23:59:59 pour inclure toute la journée
            date_to = date_to.replace(hour=23, minute=59, second=59)
            query = query.filter(Project.created_at <= date_to)
            filters_active = True
        except ValueError:
            pass
    
    # Options de tri
    sort_by = request.args.get('sort_by', 'date_desc')
    if sort_by == 'name':
        query = query.order_by(Project.name.asc())
    elif sort_by == 'date_asc':
        query = query.order_by(Project.created_at.asc())
    elif sort_by == 'date_desc':
        query = query.order_by(Project.created_at.desc())
    elif sort_by == 'credit_asc':
        query = query.order_by(Project.remaining_credit.asc())
    elif sort_by == 'credit_desc':
        query = query.order_by(Project.remaining_credit.desc())
    
    # Exécuter la requête avec pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    projects = pagination.items
    
    # Calculer le pourcentage de crédit restant pour chaque projet
    for project in projects:
        total_credit = project.get_total_credit_allocated()
        if total_credit > 0:
            project.credit_percent = (project.remaining_credit / total_credit) * 100
        else:
            project.credit_percent = 0
    
    # Récupérer tous les clients pour le filtre
    all_clients = []
    if current_user.is_admin() or current_user.is_technician():
        all_clients = Client.query.order_by(Client.name).all()
    else:
        all_clients = current_user.clients
    
    # Helper function pour le template
    def get_client_by_id(client_id):
        return Client.query.get(client_id)
    
    return render_template('projects/projects.html', 
                           projects=projects, 
                           pagination=pagination,
                           all_clients=all_clients,
                           filters_active=filters_active,
                           get_client_by_id=get_client_by_id,
                           title='Projets')

@projects.route('/clients/<int:client_id>/projects/new', methods=['GET', 'POST'])
@login_required
@client_required
def new_project(client_id):
    # Seuls les admins et techniciens peuvent créer des projets
    if current_user.is_client():
        flash('Accès refusé. Vous ne pouvez pas créer de projets.', 'danger')
        return redirect(url_for('clients.client_details', client_id=client_id))
    
    # Le reste du code reste inchangé
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
@client_required
def project_details(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Calculer le pourcentage de crédit restant
    if project.initial_credit > 0:
        project.credit_percent = (project.remaining_credit / project.initial_credit) * 100
    else:
        project.credit_percent = 0
        
    # Récupérer l'historique des crédits, trié du plus récent au plus ancien
    credit_logs = CreditLog.query.filter_by(project_id=project.id).order_by(CreditLog.created_at.desc()).all()
    
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
@client_required
def edit_project(project_id):
    # Seuls les admins et techniciens peuvent modifier des projets
    if current_user.is_client():
        flash('Accès refusé. Vous ne pouvez pas modifier de projets.', 'danger')
        return redirect(url_for('projects.project_details', project_id=project_id))
    
    # Le reste du code reste inchangé
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
@client_required
def add_credit(project_id):
    # Seuls les admins et techniciens peuvent ajouter du crédit
    if current_user.is_client():
        flash('Accès refusé. Vous ne pouvez pas ajouter de crédit.', 'danger')
        return redirect(url_for('projects.project_details', project_id=project_id))
    
    # Le reste du code reste inchangé
    project = Project.query.get_or_404(project_id)
    form = AddCreditForm()
    
    if form.validate_on_submit():
        project.add_credit(form.amount.data, form.note.data)
        db.session.commit()
        from app.utils.time_format import format_time
        flash(f'{format_time(form.amount.data)} ajoutées au crédit du projet {project.name}!', 'success')
        return redirect(url_for('projects.project_details', project_id=project.id))
        
    return render_template('projects/add_credit.html', form=form, project=project, title='Ajouter du crédit')

@projects.route('/projects/<int:project_id>/delete', methods=['POST'])
@login_required
@client_required
def delete_project(project_id):
    # Seuls les admins et techniciens peuvent supprimer des projets
    if current_user.is_client():
        flash('Accès refusé. Vous ne pouvez pas supprimer de projets.', 'danger')
        return redirect(url_for('projects.project_details', project_id=project_id))
    
    # Le reste du code reste inchangé
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