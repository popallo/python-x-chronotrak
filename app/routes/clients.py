from app import db
from app.forms.client import ClientForm
from app.models.client import Client
from app.utils.decorators import login_and_admin_required
from app.utils.route_utils import (
    apply_filters,
    apply_sorting,
    delete_from_db,
    get_accessible_clients,
    get_client_by_slug_or_id,
    save_to_db,
)
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_wtf import FlaskForm

clients = Blueprint("clients", __name__)


@clients.route("/clients")
@login_required
# @cache.cached(timeout=300, query_string=True)  # Désactivé temporairement pour le débogage
def list_clients():
    page = request.args.get("page", 1, type=int)
    per_page = 10

    # Récupérer les filtres
    filters = {"search": request.args.get("search")}

    # Appliquer les filtres avec une sous-requête optimisée
    base_query = get_accessible_clients()
    query, filters_active = apply_filters(base_query, Client, filters)

    # Appliquer le tri avec un index implicite
    sort_by = request.args.get("sort_by", "name")
    sort_order = request.args.get("sort_order", "asc")
    query = apply_sorting(query, Client, sort_by, sort_order)

    # Charger explicitement les relations avec selectinload pour les collections
    query = query.options(db.selectinload(Client.projects))

    # Pagination
    clients = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "clients/clients.html",
        clients=clients,
        filters_active=filters_active,
        sort_by=sort_by,
        sort_order=sort_order,
        title="Clients",
    )


@clients.route("/clients/new", methods=["GET", "POST"])
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
            notes=form.notes.data,
        )
        save_to_db(client)
        flash(f'Client "{form.name.data}" créé avec succès!', "success")
        return redirect(url_for("clients.list_clients"))

    return render_template("clients/client_form.html", form=form, title="Nouveau client")


@clients.route("/clients/<slug_or_id>/edit", methods=["GET", "POST"])
@login_required
def edit_client(slug_or_id):
    client = get_client_by_slug_or_id(slug_or_id)

    # Vérifier si l'utilisateur a le droit de modifier ce client
    if current_user.is_client() and not current_user.has_access_to_client(client.id):
        flash("Vous n'avez pas les permissions nécessaires pour modifier cette société.", "danger")
        return redirect(url_for("clients.client_details", slug_or_id=client.slug))

    form = ClientForm(obj=client)

    if form.validate_on_submit():
        client.name = form.name.data
        client.contact_name = form.contact_name.data
        client.email = form.email.data
        client.phone = form.phone.data
        client.address = form.address.data
        client.notes = form.notes.data
        save_to_db(client)

        flash(f'Client "{client.name}" mis à jour!', "success")
        return redirect(url_for("clients.client_details", slug_or_id=client.slug))

    # Utiliser la valeur déchiffrée pour l'email
    form.email.data = client.safe_email

    return render_template("clients/client_form.html", form=form, client=client, title="Modifier le client")


@clients.route("/clients/<slug_or_id>/delete", methods=["POST"])
@login_and_admin_required
def delete_client(slug_or_id):
    client = get_client_by_slug_or_id(slug_or_id)
    delete_from_db(client)
    flash(f'Client "{client.name}" supprimé!', "success")
    return redirect(url_for("clients.list_clients"))


@clients.route("/clients/<slug_or_id>")
@login_required
def client_details(slug_or_id):
    client = get_client_by_slug_or_id(slug_or_id)
    # Charger les projets en une seule requête (accès forcé pour éviter N+1)
    _ = client.projects
    form = FlaskForm()  # Formulaire vide pour le CSRF token
    return render_template("clients/client_detail.html", client=client, form=form)
