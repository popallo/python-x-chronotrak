import requests
from app import db
from app.forms.auth import (
    LoginForm,
    NotificationPreferenceForm,
    PasswordResetForm,
    ProfileForm,
    RegistrationForm,
    RequestResetForm,
    UserEditForm,
    UserForm,
)
from app.models.client import Client
from app.models.notification import NotificationPreference
from app.models.task import Comment, Task, TimeEntry
from app.models.token import PasswordResetToken
from app.models.user import User
from app.utils import flash_admin_required, flash_already_logged_in, flash_cannot_delete_self, get_utc_now
from app.utils.email import send_password_reset_email
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

auth = Blueprint("auth", __name__)


def verify_turnstile_token(token):
    """Vérifie le token Turnstile avec l'API Cloudflare"""
    if not current_app.config["TURNSTILE_ENABLED"]:
        return True

    if not token:
        return False

    response = requests.post(
        "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        {"secret": current_app.config["TURNSTILE_SECRET_KEY"], "response": token},
        timeout=10,  # Timeout de 10 secondes pour éviter les blocages
    )

    result = response.json()
    return result.get("success", False)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        # Vérifier le token Turnstile si activé
        if current_app.config["TURNSTILE_ENABLED"]:
            token = request.form.get("cf-turnstile-response")
            if not verify_turnstile_token(token):
                flash("Veuillez compléter la vérification Turnstile.", "danger")
                return render_template("auth/login.html", form=form, title="Connexion")

        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            # Mise à jour de la date de dernière connexion (convertir en naive pour SQLite)
            user.last_login = get_utc_now().replace(tzinfo=None)
            db.session.commit()

            next_page = request.args.get("next")
            return redirect(next_page if next_page else url_for("main.dashboard"))
        else:
            flash("Échec de la connexion. Vérifiez votre email et mot de passe.", "danger")

    return render_template("auth/login.html", form=form, title="Connexion")


@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth.route("/register", methods=["GET", "POST"])
@login_required
def register():
    # Seuls les administrateurs peuvent créer de nouveaux comptes
    if not current_user.is_admin():
        flash_admin_required()
        return redirect(url_for("main.dashboard"))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(name=form.name.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)

        # Si l'utilisateur est un client, associer les clients sélectionnés
        if form.role.data == "client" and form.clients.data:
            for client_id in form.clients.data:
                client = Client.query.get(client_id)
                if client:
                    user.clients.append(client)

        db.session.commit()
        flash(f"Compte créé pour {form.name.data}!", "success")
        return redirect(url_for("auth.users"))

    return render_template("auth/register.html", form=form, title="Nouvel utilisateur")


@auth.route("/users")
@login_required
def users():
    # Seuls les administrateurs peuvent voir la liste des utilisateurs
    if not current_user.is_admin():
        flash_admin_required()
        return redirect(url_for("main.dashboard"))

    users = User.query.all()
    form = UserForm()
    return render_template("auth/users.html", users=users, form=form, title="Utilisateurs")


@auth.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm()

    # Obtenir ou créer les préférences de notification
    if not current_user.notification_preferences:
        preferences = NotificationPreference(user_id=current_user.id)
        db.session.add(preferences)
        db.session.commit()
    else:
        preferences = current_user.notification_preferences

    # Initialiser le formulaire des préférences
    notif_form = NotificationPreferenceForm(obj=preferences)

    if form.validate_on_submit():
        current_user.name = form.name.data

        if form.password.data:
            current_user.set_password(form.password.data)

        db.session.commit()
        flash("Votre profil a été mis à jour!", "success")
        return redirect(url_for("auth.profile"))
    elif request.method == "GET":
        form.name.data = current_user.name
        form.email.data = current_user.email

    return render_template("auth/profile.html", form=form, notif_form=notif_form, title="Mon profil")


@auth.route("/profile/notifications", methods=["POST"])
@login_required
def notification_preferences():
    # Obtenir ou créer les préférences de notification
    if not current_user.notification_preferences:
        preferences = NotificationPreference(user_id=current_user.id)
        db.session.add(preferences)
    else:
        preferences = current_user.notification_preferences

    form = NotificationPreferenceForm()

    if form.validate_on_submit():
        # Mettre à jour les préférences
        preferences.email_notifications_enabled = form.email_notifications_enabled.data
        preferences.task_status_change = form.task_status_change.data
        preferences.task_comment_added = form.task_comment_added.data
        preferences.task_time_logged = form.task_time_logged.data
        preferences.project_credit_low = form.project_credit_low.data

        db.session.commit()
        flash("Vos préférences de notification ont été mises à jour!", "success")

    return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html", form=form, title="Mon profil")


@auth.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id):
    # Vérifier les droits administrateur
    if not current_user.is_admin():
        flash_admin_required()
        return redirect(url_for("main.dashboard"))

    # Empêcher l'admin de supprimer son propre compte
    if current_user.id == user_id:
        flash_cannot_delete_self()
        return redirect(url_for("auth.users"))

    user = User.query.get_or_404(user_id)

    # Pour les utilisateurs de type client, vérifier s'ils sont liés à des tâches
    tasks_assigned = Task.query.filter_by(user_id=user.id).count()
    if tasks_assigned > 0:
        flash(f"Impossible de supprimer cet utilisateur car {tasks_assigned} tâche(s) lui sont assignées.", "danger")
        return redirect(url_for("auth.users"))

    # Vérifier les entrées de temps
    time_entries = TimeEntry.query.filter_by(user_id=user.id).count()
    if time_entries > 0:
        flash(
            f"Impossible de supprimer cet utilisateur car {time_entries} entrée(s) de temps lui sont associées.",
            "danger",
        )
        return redirect(url_for("auth.users"))

    # Vérifier les commentaires
    comments = Comment.query.filter_by(user_id=user.id).count()
    if comments > 0:
        flash(f"Impossible de supprimer cet utilisateur car {comments} commentaire(s) lui sont associés.", "danger")
        return redirect(url_for("auth.users"))

    # Si tout est OK, supprimer l'utilisateur
    db.session.delete(user)
    db.session.commit()
    flash(f"Utilisateur {user.name} supprimé avec succès!", "success")
    return redirect(url_for("auth.users"))


@auth.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    # Vérifier les droits administrateur
    if not current_user.is_admin():
        flash_admin_required()
        return redirect(url_for("main.dashboard"))

    user = User.query.get_or_404(user_id)
    form = UserEditForm(original_email=user.email)

    if form.validate_on_submit():
        user.name = form.name.data
        user.email = form.email.data
        user.role = form.role.data

        # Gérer les associations client seulement si c'est un utilisateur de type client
        if form.role.data == "client":
            # Vider les associations actuelles
            user.clients = []
            # Ajouter les nouvelles associations
            if form.clients.data:
                for client_id in form.clients.data:
                    client = Client.query.get(client_id)
                    if client:
                        user.clients.append(client)

        # Modifier le mot de passe si fourni
        if form.password.data:
            user.set_password(form.password.data)

        db.session.commit()
        flash(f"Utilisateur {user.name} mis à jour avec succès!", "success")
        return redirect(url_for("auth.users"))

    elif request.method == "GET":
        form.name.data = user.name
        form.email.data = user.email
        form.role.data = user.role
        # Pré-remplir les clients sélectionnés
        if user.role == "client":
            form.clients.data = [client.id for client in user.clients]

    return render_template("auth/edit_user.html", form=form, user=user, title="Modifier utilisateur")


@auth.route("/users/<int:user_id>/send_access", methods=["POST"])
@login_required
def send_user_access(user_id):
    """Envoie un mail avec lien de définition/réinitialisation de mot de passe"""
    # Vérifier les droits administrateur
    if not current_user.is_admin():
        flash_admin_required()
        return redirect(url_for("main.dashboard"))

    user = User.query.get_or_404(user_id)

    # Déterminer s'il s'agit d'un nouveau compte (n'a jamais défini de mot de passe)
    # On vérifie si l'utilisateur s'est déjà connecté au moins une fois
    is_new_account = user.last_login is None

    # Envoyer l'email
    if send_password_reset_email(user, is_new_account):
        flash(f"Informations d'accès envoyées à {user.email}", "success")
    else:
        flash("Erreur lors de l'envoi des informations d'accès", "danger")

    # Rediriger vers la page d'édition de l'utilisateur
    return redirect(url_for("auth.edit_user", user_id=user.id))


@auth.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Page de réinitialisation de mot de passe avec un jeton"""
    # Vérifier si l'utilisateur est déjà connecté
    if current_user.is_authenticated:
        flash_already_logged_in()
        return redirect(url_for("main.dashboard"))

    # Vérifier la validité du jeton
    token_record = PasswordResetToken.get_valid_token(token)

    token_expired = False
    is_new_account = False

    if token_record:
        # Récupérer l'utilisateur associé au jeton
        user = User.query.get(token_record.user_id)

        # Vérifier si c'est un nouveau compte (jamais connecté)
        is_new_account = user.last_login is None

        form = PasswordResetForm()

        if form.validate_on_submit():
            user.set_password(form.password.data)
            token_record.mark_as_used()
            db.session.commit()

            # Rediriger vers la page de confirmation
            return redirect(url_for("auth.reset_success", is_new=is_new_account))

        return render_template(
            "auth/reset_password.html", form=form, token_valid=True, token_expired=False, is_new_account=is_new_account
        )
    else:
        # Vérifier si le jeton existe mais est expiré
        expired_token = PasswordResetToken.query.filter_by(token=token).first()
        token_expired = expired_token is not None

        return render_template(
            "auth/reset_password.html", token_valid=False, token_expired=token_expired, is_new_account=False
        )


@auth.route("/reset_success")
def reset_success():
    """Page de confirmation après réinitialisation réussie"""
    is_new = request.args.get("is_new", "false").lower() == "true"
    return render_template("auth/reset_success.html", is_new_account=is_new)


@auth.route("/reset_password_request", methods=["GET", "POST"])
def reset_request():
    """Page de demande de réinitialisation du mot de passe"""
    # Vérifier si l'utilisateur est déjà connecté
    if current_user.is_authenticated:
        flash_already_logged_in()
        return redirect(url_for("main.dashboard"))

    form = RequestResetForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        # Même si l'utilisateur n'existe pas, nous ne le signalons pas
        # Cela évite de révéler quels emails sont enregistrés
        if user:
            send_password_reset_email(user)

        # Rediriger vers la page de confirmation (même si l'email n'existe pas)
        return redirect(url_for("auth.reset_request_sent"))

    return render_template("auth/request_reset.html", form=form, title="Mot de passe oublié")


@auth.route("/reset_request_sent")
def reset_request_sent():
    """Page de confirmation d'envoi de demande de réinitialisation"""
    return render_template("auth/reset_request_sent.html", title="Email envoyé")


@auth.route("/users/<int:user_id>/impersonate")
@login_required
def impersonate_user(user_id):
    # Vérifier que l'utilisateur actuel est admin ou technicien
    if not (current_user.is_admin() or current_user.is_technician()):
        flash("Accès refusé. Droits administrateur ou technicien requis.", "danger")
        return redirect(url_for("main.dashboard"))

    # Récupérer l'utilisateur cible
    target_user = User.query.get_or_404(user_id)

    # Vérifier que l'utilisateur cible n'est pas un admin
    if target_user.is_admin():
        flash("Vous ne pouvez pas vous connecter en tant qu'administrateur.", "danger")
        return redirect(url_for("auth.users"))

    # Stocker l'ID de l'utilisateur original dans la session
    session["original_user_id"] = current_user.id

    # Se connecter en tant que l'utilisateur cible
    login_user(target_user)
    flash(f"Vous êtes maintenant connecté en tant que {target_user.name}.", "info")
    return redirect(url_for("main.dashboard"))


@auth.route("/stop-impersonating")
@login_required
def stop_impersonating():
    if "original_user_id" not in session:
        flash("Vous n'êtes pas en train d'impersonner un autre utilisateur.", "warning")
        return redirect(url_for("main.dashboard"))

    # Récupérer l'utilisateur original
    original_user = User.query.get(session["original_user_id"])
    if not original_user:
        flash("Erreur lors de la récupération de votre compte.", "danger")
        return redirect(url_for("auth.logout"))

    # Supprimer l'ID de l'utilisateur original de la session
    session.pop("original_user_id", None)

    # Se reconnecter en tant qu'utilisateur original
    login_user(original_user)
    flash("Vous êtes revenu à votre compte.", "info")
    return redirect(url_for("main.dashboard"))
