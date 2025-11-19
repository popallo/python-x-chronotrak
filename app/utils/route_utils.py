from flask_login import current_user
from app.models.client import Client
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.models.communication import Communication
from app import db
from sqlalchemy import or_, and_, func
from datetime import datetime
from flask import abort

def get_client_by_id(client_id):
    return Client.query.get_or_404(client_id)

def get_client_by_slug_or_id(slug_or_id):
    # Si c'est un entier, recherche par ID
    try:
        client_id = int(slug_or_id)
        client = Client.query.get(client_id)
        if client:
            if current_user.is_client() and not current_user.has_access_to_client(client.id):
                abort(403)
            return client
    except (ValueError, TypeError):
        pass
    # Sinon, recherche par slug
    client = Client.query.filter_by(slug=slug_or_id).first()
    if not client:
        abort(404)
    if current_user.is_client() and not current_user.has_access_to_client(client.id):
        abort(403)
    return client

def get_project_by_id(project_id):
    project = Project.query.get_or_404(project_id)
    if current_user.is_client() and not current_user.has_access_to_client(project.client_id):
        from flask import abort
        abort(403)
    return project

def get_project_by_slug_or_id(slug_or_id):
    # Si c'est un entier, recherche par ID
    try:
        project_id = int(slug_or_id)
        project = Project.query.get(project_id)
        if project:
            if current_user.is_client() and not current_user.has_access_to_client(project.client_id):
                abort(403)
            return project
    except (ValueError, TypeError):
        pass
    # Sinon, recherche par slug
    project = Project.query.filter_by(slug=slug_or_id).first()
    if not project:
        abort(404)
    if current_user.is_client() and not current_user.has_access_to_client(project.client_id):
        abort(403)
    return project

def get_task_by_id(task_id):
    return Task.query.get_or_404(task_id)

def get_task_by_slug_or_id(slug_or_id):
    # Si c'est un entier, recherche par ID
    try:
        task_id = int(slug_or_id)
        task = Task.query.get(task_id)
        if task:
            if current_user.is_client() and not current_user.has_access_to_client(task.project.client_id):
                abort(403)
            return task
    except (ValueError, TypeError):
        pass
    # Sinon, recherche par slug
    task = Task.query.filter_by(slug=slug_or_id).first()
    if not task:
        abort(404)
    if current_user.is_client() and not current_user.has_access_to_client(task.project.client_id):
        abort(403)
    return task

def get_accessible_clients():
    """Récupère les clients accessibles à l'utilisateur"""
    if current_user.is_admin() or current_user.is_technician():
        return Client.query
    return Client.query.filter(Client.id.in_([client.id for client in current_user.clients]))

def get_accessible_projects():
    """Récupère les projets accessibles à l'utilisateur"""
    if current_user.is_admin() or current_user.is_technician():
        return Project.query
    client_ids = [client.id for client in current_user.clients]
    return Project.query.filter(Project.client_id.in_(client_ids))

def save_to_db(obj):
    db.session.add(obj)
    db.session.commit()

def delete_from_db(obj):
    try:
        db.session.delete(obj)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise

def get_user_by_id(user_id):
    return User.query.get_or_404(user_id)

def get_communication_by_id(comm_id):
    return Communication.query.get_or_404(comm_id)

def apply_filters(query, model, filters):
    """Applique les filtres à une requête"""
    filters_active = False
    
    for field, value in filters.items():
        if value is not None:
            if field == 'search' and hasattr(model, 'name'):
                query = query.filter(model.name.ilike(f'%{value}%'))
                filters_active = True
            elif field == 'search' and hasattr(model, 'title'):
                query = query.filter(model.title.ilike(f'%{value}%'))
                filters_active = True
            elif field == 'client_id' and hasattr(model, 'client_id'):
                query = query.filter(model.client_id == value)
                filters_active = True
            elif field == 'project_id' and hasattr(model, 'project_id'):
                query = query.filter(model.project_id == value)
                filters_active = True
            elif field == 'priority' and hasattr(model, 'priority'):
                query = query.filter(model.priority == value)
                filters_active = True
            elif field == 'favorites_only' and hasattr(model, 'is_favorite'):
                if value == 'true':
                    query = query.filter(model.is_favorite == True)
                elif value == 'false':
                    query = query.filter(model.is_favorite == False)
                filters_active = True
            elif field == 'credit_status' and hasattr(model, 'remaining_credit'):
                if value == 'critical':
                    query = query.filter(model.remaining_credit < 120)
                elif value == 'low':
                    query = query.filter(model.remaining_credit < 300, model.remaining_credit >= 120)
                elif value == 'normal':
                    query = query.filter(model.remaining_credit >= 300)
                filters_active = True
            elif field == 'type' and hasattr(model, 'type'):
                query = query.filter(model.type == value)
                filters_active = True
            elif field == 'recipient' and hasattr(model, 'recipient'):
                query = query.filter(model.recipient.ilike(f'%{value}%'))
                filters_active = True
            elif field == 'date_from' and hasattr(model, 'sent_at'):
                try:
                    date_from = datetime.strptime(value, '%Y-%m-%d')
                    query = query.filter(model.sent_at >= date_from)
                    filters_active = True
                except ValueError:
                    pass
            elif field == 'date_to' and hasattr(model, 'sent_at'):
                try:
                    date_to = datetime.strptime(value, '%Y-%m-%d')
                    date_to = date_to.replace(hour=23, minute=59, second=59)
                    query = query.filter(model.sent_at <= date_to)
                    filters_active = True
                except ValueError:
                    pass
    
    return query, filters_active

def apply_sorting(query, model, sort_by, sort_order='asc'):
    """Applique le tri à une requête"""
    if sort_by == 'name' and hasattr(model, 'name'):
        query = query.order_by(model.name.asc() if sort_order == 'asc' else model.name.desc())
    elif sort_by == 'client' and hasattr(model, 'client_id'):
        query = query.join(Client).order_by(Client.name.asc() if sort_order == 'asc' else Client.name.desc())
    elif sort_by == 'remaining_credit' and hasattr(model, 'remaining_credit'):
        query = query.order_by(model.remaining_credit.asc() if sort_order == 'asc' else model.remaining_credit.desc())
    elif sort_by == 'created_at' and hasattr(model, 'created_at'):
        query = query.order_by(model.created_at.asc() if sort_order == 'asc' else model.created_at.desc())
    
    return query 