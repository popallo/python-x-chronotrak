from datetime import timedelta

from app import db
from app.forms.client import ClientForm
from app.models.client import Client
from app.models.project import Project
from app.utils import get_utc_now
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
from sqlalchemy import func

clients = Blueprint("clients", __name__)


@clients.route("/clients")
@login_required
def list_clients():
    page = request.args.get("page", 1, type=int)
    per_page = 10

    filters = {
        "search": request.args.get("search"),
        "date_from": request.args.get("date_from"),
        "date_to": request.args.get("date_to"),
    }

    query = get_accessible_clients()
    query, filters_active = apply_filters(query, Client, filters)

    has_projects = request.args.get("has_projects")
    if has_projects == "true":
        query = query.filter(Client.projects.any())
        filters_active = True
    elif has_projects == "false":
        query = query.filter(~Client.projects.any())
        filters_active = True

    # Stats sur le jeu filtré (avant tri par projets / pagination)
    one_month_ago = (get_utc_now() - timedelta(days=30)).replace(tzinfo=None)
    stats_total = query.count()
    stats_with_projects = query.filter(Client.projects.any()).count()
    stats_without_projects = query.filter(~Client.projects.any()).count()
    stats_recent = query.filter(Client.created_at >= one_month_ago).count()

    sort_by = request.args.get("sort_by", "name")
    sort_order = request.args.get("sort_order", "asc")

    if sort_by in ("projects_asc", "projects_desc"):
        project_count_subq = (
            db.session.query(Project.client_id, func.count(Project.id).label("project_count"))
            .group_by(Project.client_id)
            .subquery()
        )
        query = query.outerjoin(project_count_subq, Client.id == project_count_subq.c.client_id)
        count_expr = func.coalesce(project_count_subq.c.project_count, 0)
        query = query.order_by(count_expr.asc() if sort_by == "projects_asc" else count_expr.desc(), Client.name.asc())
    else:
        sort_map = {
            "name": ("name", "asc"),
            "date_asc": ("created_at", "asc"),
            "date_desc": ("created_at", "desc"),
        }
        mapped_field, mapped_order = sort_map.get(sort_by, ("name", "asc"))
        query = apply_sorting(query, Client, mapped_field, mapped_order)

    query = query.options(db.selectinload(Client.projects))
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    entity_title = "Sociétés" if current_user.is_client() else "Clients"

    return render_template(
        "clients/clients.html",
        pagination=pagination,
        filters_active=filters_active,
        sort_by=sort_by,
        sort_order=sort_order,
        stats_total=stats_total,
        stats_with_projects=stats_with_projects,
        stats_without_projects=stats_without_projects,
        stats_recent=stats_recent,
        title=entity_title,
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
