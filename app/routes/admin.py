from app import db
from app.forms.admin import TestEmailForm, TimeTransferForm
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.utils.decorators import login_and_admin_required
from app.utils.email import send_email
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user

admin = Blueprint("admin", __name__, url_prefix="/admin")


@admin.before_request
def require_admin():
    if not current_user.is_authenticated or not current_user.is_admin():
        flash("Accès refusé. Droits administrateur requis.", "danger")
        return redirect(url_for("main.dashboard"))


def send_test_email(recipient):
    """Envoie un email de test à l'adresse spécifiée"""
    try:
        subject = "ChronoTrak - Test de configuration SMTP"
        text_body = "Ceci est un email de test envoyé depuis ChronoTrak. Si vous recevez cet email, la configuration SMTP fonctionne correctement."
        html_body = "<h1>ChronoTrak - Test de configuration SMTP</h1><p>Ceci est un email de test envoyé depuis ChronoTrak. Si vous recevez cet email, la configuration SMTP fonctionne correctement.</p>"

        # Utiliser la logique centralisée de send_email
        success = send_email(subject, [recipient], text_body, html_body, email_type="test")

        if success:
            return True, None
        else:
            return False, "Échec de l'envoi de l'email"
    except Exception as e:
        return False, str(e)


@admin.route("/tasks")
@login_and_admin_required
def list_tasks():
    try:
        # Récupération des paramètres de filtrage
        statuses = request.args.getlist("status")  # Récupère la liste des statuts sélectionnés
        priority = request.args.get("priority")
        project_id = request.args.get("project_id", type=int)
        user_id = request.args.get("user_id", type=int)
        page = request.args.get("page", 1, type=int)
        per_page = 10  # Nombre de tâches par page

        # Construction de la requête de base
        query = Task.query.order_by(Task.created_at.desc())

        # Application des filtres
        if statuses:  # Si des statuts sont sélectionnés
            query = query.filter(Task.status.in_(statuses))
        if priority:
            query = query.filter(Task.priority == priority)
        if project_id:
            query = query.filter(Task.project_id == project_id)
        if user_id:
            query = query.filter(Task.user_id == user_id)

        # Pagination
        tasks = query.paginate(page=page, per_page=per_page, error_out=False)

        # Récupération des projets et utilisateurs pour les filtres
        projects = Project.query.order_by(Project.name).all()
        users = User.query.filter(User.role != "client").order_by(User.name).all()

        # Préparation des paramètres de requête pour la pagination
        query_params = {}
        if statuses:
            query_params["status"] = statuses
        if priority:
            query_params["priority"] = priority
        if project_id:
            query_params["project_id"] = project_id
        if user_id:
            query_params["user_id"] = user_id

        return render_template(
            "admin/tasks.html",
            tasks=tasks,
            projects=projects,
            users=users,
            query_params=query_params,
            title="Gestion des tâches",
        )
    except Exception as e:
        flash(f"Une erreur est survenue : {str(e)}", "danger")
        return redirect(url_for("admin.list_tasks"))


@admin.route("/test-email", methods=["GET", "POST"])
@login_and_admin_required
def test_email():
    form = TestEmailForm()

    if form.validate_on_submit():
        success, error = send_test_email(form.recipient.data)
        if success:
            flash(f"Email de test envoyé à {form.recipient.data}. Vérifiez votre boîte de réception.", "success")
        else:
            flash(f"Erreur lors de l'envoi de l'email: {error}", "danger")
        return redirect(url_for("admin.test_email"))

    # Récupérer la configuration SMTP pour l'afficher
    smtp_config = {
        "MAIL_SERVER": current_app.config.get("MAIL_SERVER"),
        "MAIL_PORT": current_app.config.get("MAIL_PORT"),
        "MAIL_USE_TLS": current_app.config.get("MAIL_USE_TLS"),
        "MAIL_USE_SSL": current_app.config.get("MAIL_USE_SSL"),
        "MAIL_USERNAME": current_app.config.get("MAIL_USERNAME"),
        "MAIL_DEFAULT_SENDER": current_app.config.get("MAIL_DEFAULT_SENDER"),
    }

    return render_template("admin/test_email.html", form=form, config=smtp_config, title="Test SMTP")


@admin.route("/time-transfer", methods=["GET", "POST"])
@login_and_admin_required
def time_transfer():
    form = TimeTransferForm()

    # Récupérer tous les projets pour les listes déroulantes
    projects = Project.query.order_by(Project.name).all()
    form.source_project_id.choices = [(p.id, f"{p.name} ({p.client.name})") for p in projects]
    form.target_project_id.choices = [(p.id, f"{p.name} ({p.client.name})") for p in projects]

    if form.validate_on_submit():
        source_project = Project.query.get(form.source_project_id.data)
        target_project = Project.query.get(form.target_project_id.data)

        # Vérifier que les projets appartiennent au même client
        if source_project.client_id != target_project.client_id:
            flash("Les projets doivent appartenir au même client.", "danger")
            return render_template("admin/time_transfer.html", form=form, title="Transfert de temps")

        # Vérifier qu'il y a assez de crédit
        if source_project.remaining_credit < form.amount.data:
            flash("Le projet source n'a pas assez de crédit disponible.", "danger")
            return render_template("admin/time_transfer.html", form=form, title="Transfert de temps")

        try:
            # Créer une tâche pour le projet source
            source_task = Task(
                title=f"Transfert de {form.amount.data}h vers {target_project.name}",
                description=form.description.data
                or f"Transfert de {form.amount.data}h vers le projet {target_project.name}",
                project_id=source_project.id,
                user_id=current_user.id,
                status="terminé",
                priority="normale",
            )
            db.session.add(source_task)

            # Créer une tâche pour le projet destination
            target_task = Task(
                title=f"Réception de {form.amount.data}h depuis {source_project.name}",
                description=form.description.data
                or f"Réception de {form.amount.data}h depuis le projet {source_project.name}",
                project_id=target_project.id,
                user_id=current_user.id,
                status="terminé",
                priority="normale",
            )
            db.session.add(target_task)

            # Flush pour obtenir les IDs des tâches avant de créer les logs de crédit
            db.session.flush()

            # Déduire le crédit du projet source
            source_project.deduct_credit(
                form.amount.data, task_id=source_task.id, note=f"Transfert vers {target_project.name}"
            )

            # Ajouter le crédit au projet destination
            target_project.add_credit(form.amount.data, f"Transfert depuis {source_project.name}")

            db.session.commit()
            flash("Transfert de temps effectué avec succès!", "success")
            return redirect(url_for("admin.time_transfer"))

        except Exception as e:
            db.session.rollback()
            flash(f"Une erreur est survenue lors du transfert : {str(e)}", "danger")
            return render_template("admin/time_transfer.html", form=form, title="Transfert de temps")

    return render_template("admin/time_transfer.html", form=form, title="Transfert de temps")
