from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.client import Client
from app.forms.client import ClientForm
from app.utils.decorators import login_and_client_required, login_and_admin_required
from app.utils.route_utils import (
    get_client_by_id,
    get_accessible_clients,
    save_to_db,
    delete_from_db,
    apply_filters,
    apply_sorting
)

clients = Blueprint('clients', __name__)

@clients.route('/clients')
@login_required
def list_clients():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Récupérer les filtres
    filters = {
        'search': request.args.get('search')
    }
    
    # Appliquer les filtres
    query = get_accessible_clients()
    query, filters_active = apply_filters(query, Client, filters)
    
    # Appliquer le tri
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')
    query = apply_sorting(query, Client, sort_by, sort_order)
    
    clients = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('clients/clients.html', 
                         clients=clients,
                         filters_active=filters_active,
                         sort_by=sort_by,
                         sort_order=sort_order,
                         title='Clients')

@clients.route('/clients/new', methods=['GET', 'POST'])
@login_and_admin_required
def new_client():
    form = ClientForm()
    if form.validate_on_submit():
        client = Client(
            name=form.name.data,
            contact_name=form.contact_name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            notes=form.notes.data
        )
        save_to_db(client)
        flash(f'Client "{form.name.data}" créé avec succès!', 'success')
        return redirect(url_for('clients.list_clients'))
        
    return render_template('clients/client_form.html', form=form, title='Nouveau client')

@clients.route('/clients/<int:client_id>/edit', methods=['GET', 'POST'])
@login_and_admin_required
def edit_client(client_id):
    client = get_client_by_id(client_id)
    form = ClientForm(obj=client)
    
    if form.validate_on_submit():
        client.name = form.name.data
        client.contact_name = form.contact_name.data
        client.email = form.email.data
        client.phone = form.phone.data
        client.address = form.address.data
        client.notes = form.notes.data
        save_to_db(client)
        
        flash(f'Client "{client.name}" mis à jour!', 'success')
        return redirect(url_for('clients.client_details', client_id=client.id))
    
    # Utiliser la valeur déchiffrée pour l'email
    form.email.data = client.safe_email
    
    return render_template('clients/client_form.html', form=form, client=client, title='Modifier le client')

@clients.route('/clients/<int:client_id>/delete', methods=['POST'])
@login_and_admin_required
def delete_client(client_id):
    client = get_client_by_id(client_id)
    delete_from_db(client)
    flash(f'Client "{client.name}" supprimé!', 'success')
    return redirect(url_for('clients.list_clients'))

@clients.route('/clients/<int:client_id>')
@login_required
@login_and_client_required
def client_details(client_id):
    client = get_client_by_id(client_id)
    return render_template('clients/client_detail.html', client=client)