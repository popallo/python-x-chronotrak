from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.client import Client
from app.forms.client import ClientForm

clients = Blueprint('clients', __name__)

@clients.route('/clients')
@login_required
def list_clients():
    all_clients = Client.query.order_by(Client.name).all()
    return render_template('clients/clients.html', clients=all_clients, title='Clients')

@clients.route('/clients/new', methods=['GET', 'POST'])
@login_required
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
        db.session.add(client)
        db.session.commit()
        flash(f'Client {form.name.data} créé avec succès!', 'success')
        return redirect(url_for('clients.list_clients'))
        
    return render_template('clients/client_form.html', form=form, title='Nouveau client')

@clients.route('/clients/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    form = ClientForm()
    
    if form.validate_on_submit():
        client.name = form.name.data
        client.contact_name = form.contact_name.data
        client.email = form.email.data
        client.phone = form.phone.data
        client.address = form.address.data
        client.notes = form.notes.data
        
        db.session.commit()
        flash(f'Client {client.name} mis à jour avec succès!', 'success')
        return redirect(url_for('clients.list_clients'))
        
    elif request.method == 'GET':
        form.name.data = client.name
        form.contact_name.data = client.contact_name
        form.email.data = client.email
        form.phone.data = client.phone
        form.address.data = client.address
        form.notes.data = client.notes
        
    return render_template('clients/client_form.html', form=form, client=client, title='Modifier client')

@clients.route('/clients/<int:client_id>/delete', methods=['POST'])
@login_required
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    
    # Vérifier s'il y a des projets liés
    if client.projects:
        flash(f'Impossible de supprimer le client {client.name} car des projets lui sont associés.', 'danger')
        return redirect(url_for('clients.list_clients'))
        
    db.session.delete(client)
    db.session.commit()
    flash(f'Client {client.name} supprimé avec succès!', 'success')
    return redirect(url_for('clients.list_clients'))

@clients.route('/clients/<int:client_id>')
@login_required
def client_details(client_id):
    client = Client.query.get_or_404(client_id)
    return render_template('clients/client_detail.html', client=client, title=client.name)