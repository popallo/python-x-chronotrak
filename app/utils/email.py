import queue
from threading import Thread

from flask import current_app, render_template, url_for
from flask_mail import Message

from app import db, mail
from app.models.communication import Communication
from app.models.user import User
from app.utils.time_format import format_time

# Queue pour les emails à envoyer de façon asynchrone
email_queue = queue.Queue()


def email_worker():
    """Worker thread pour traiter la queue d'emails"""
    while True:
        try:
            # Attendre un email à traiter (timeout de 5 secondes)
            email_data = email_queue.get(timeout=5)
            if email_data is None:  # Signal d'arrêt
                break

            # Traiter l'email sans timeout complexe
            send_async_email(email_data["app"], email_data["msg"], email_data["email_data"])
            email_queue.task_done()

        except queue.Empty:
            # Pas d'email à traiter, continuer
            continue
        except Exception as e:
            current_app.logger.error(f"Erreur dans le worker email: {e}")
            if "email_data" in locals():
                email_queue.task_done()


# Démarrer le worker email au démarrage de l'application
email_worker_thread = None


def start_email_worker():
    """Démarre le worker email"""
    global email_worker_thread
    if email_worker_thread is None or not email_worker_thread.is_alive():
        email_worker_thread = Thread(target=email_worker, daemon=True)
        email_worker_thread.start()


def send_async_email(app, msg, email_data=None):
    """Envoie un email de façon asynchrone"""
    with app.app_context():
        try:
            # Timeout de 15 secondes pour l'envoi d'email (augmenté)
            import socket

            socket.setdefaulttimeout(15)

            # Vérifier la taille de la queue avant d'envoyer
            queue_size = email_queue.qsize()
            if queue_size > 100:  # Si trop d'emails en attente
                current_app.logger.warning(f"Queue d'emails surchargée ({queue_size} emails), email ignoré")
                return

            mail.send(msg)
            current_app.logger.info(f"Email envoyé avec succès: {msg.subject}")
        except TimeoutError:
            current_app.logger.error(f"Timeout lors de l'envoi de l'email: {msg.subject}")
        except Exception as e:
            current_app.logger.error(f"Erreur lors de l'envoi de l'email: {e}")
            # Enregistrer l'échec en base si on a les données
            if email_data:
                try:
                    from app.models.communication import Communication

                    comm = Communication(
                        recipient=email_data.get("recipient", "unknown"),
                        subject=email_data.get("subject", "Unknown"),
                        content_html=email_data.get("html_body", ""),
                        content_text=email_data.get("text_body", ""),
                        type=email_data.get("email_type", "general"),
                        status="failed",
                        user_id=email_data.get("user_id"),
                        task_id=email_data.get("task_id"),
                        project_id=email_data.get("project_id"),
                        triggered_by_id=email_data.get("triggered_by_id"),
                    )
                    db.session.add(comm)
                    db.session.commit()
                except Exception as db_error:
                    current_app.logger.error(f"Erreur lors de l'enregistrement de l'échec: {db_error}")


# Dans app/utils/email.py, modifions la fonction send_email


def send_email(
    subject,
    recipients,
    text_body,
    html_body,
    sender=None,
    email_type=None,
    user_id=None,
    task_id=None,
    project_id=None,
    triggered_by_id=None,
):
    """Envoie un email aux destinataires spécifiés et l'enregistre dans la base de données"""
    if not current_app.config.get("MAIL_SERVER"):
        current_app.logger.warning("Configuration SMTP manquante - email non envoyé")
        return False

    # Récupérer tous les administrateurs
    admin_users = User.query.filter_by(role="admin").all()
    admin_emails = [admin.email for admin in admin_users if admin.email]

    # Déterminer l'environnement
    flask_env = current_app.config.get("FLASK_ENV")
    is_production = flask_env == "production"

    # Log pour déboguer
    current_app.logger.info(f"Email - FLASK_ENV: {flask_env}, is_production: {is_production}")

    if not is_production:
        # En environnement non-production (dev/local), rediriger tous les emails vers les administrateurs uniquement
        if admin_emails:
            # Ajouter des infos pour identifier les destinataires initiaux
            subject = f"[{current_app.config.get('FLASK_ENV', 'DEV').upper()}] {subject} (pour {', '.join(recipients)})"
            recipients = admin_emails
            current_app.logger.info(f"Email redirigé vers les administrateurs: {', '.join(admin_emails)}")
    else:
        # En production, appliquer les règles spécifiques
        final_recipients = set(recipients)  # Utiliser un set pour éviter les doublons

        # Règle 1: Ajouter les administrateurs en copie sauf s'ils sont les seuls destinataires initiaux
        if admin_emails and set(recipients) != set(admin_emails):
            final_recipients.update(admin_emails)
            current_app.logger.info(f"Administrateurs ajoutés en copie: {', '.join(admin_emails)}")

        # Règle 2: Pour les emails liés à un projet, s'assurer que le client reçoit l'email
        # Ne pas ajouter les clients pour les emails de type task_* car send_task_notification
        # gère déjà cela avec le paramètre notify_all
        if project_id and not (email_type and email_type.startswith("task_")):
            from app.models.project import Project

            project = Project.query.get(project_id)
            if project and project.client_id:
                # Trouver les utilisateurs clients qui ont accès à ce projet
                client_users = User.query.filter_by(role="client").all()
                for client_user in client_users:
                    if client_user.has_access_to_client(project.client_id):
                        if (
                            client_user.notification_preferences
                            and client_user.notification_preferences.email_notifications_enabled
                        ):
                            # Vérifier les préférences selon le type d'email
                            prefs = client_user.notification_preferences
                            should_notify = True

                            if email_type:
                                if email_type == "project_low_credit" and not prefs.project_credit_low:
                                    should_notify = False

                            if should_notify and client_user.email not in final_recipients:
                                final_recipients.add(client_user.email)
                                current_app.logger.info(f"Client ajouté aux destinataires: {client_user.email}")

        recipients = list(final_recipients)

    # Créer UN SEUL message avec tous les destinataires
    msg = Message(subject, recipients=recipients, sender=sender or current_app.config["MAIL_DEFAULT_SENDER"])
    msg.body = text_body
    msg.html = html_body

    # Préparer les données pour l'envoi asynchrone
    email_data = {
        "subject": subject,
        "text_body": text_body,
        "html_body": html_body,
        "email_type": email_type or "general",
        "user_id": user_id,
        "task_id": task_id,
        "project_id": project_id,
        "triggered_by_id": triggered_by_id,
    }

    success = True

    try:
        # Démarrer le worker email si nécessaire
        start_email_worker()

        # Ajouter UN SEUL message à la queue (avec tous les destinataires)
        # Cela évite les doublons tout en permettant de voir tous les destinataires
        queue_data = {"app": current_app._get_current_object(), "msg": msg, "email_data": email_data}
        email_queue.put(queue_data)

    except Exception as e:
        current_app.logger.error(f"Erreur lors de l'ajout de l'email à la queue: {e}")
        success = False

    # Enregistrer la communication dans la base de données de façon asynchrone aussi
    try:

        def save_communication(app_instance):
            with app_instance.app_context():
                try:
                    for recipient in recipients:
                        comm = Communication(
                            recipient=recipient,
                            subject=subject,
                            content_html=html_body,
                            content_text=text_body,
                            type=email_type or "general",
                            status="sent" if success else "failed",
                            user_id=user_id,
                            task_id=task_id,
                            project_id=project_id,
                            triggered_by_id=triggered_by_id,
                        )
                        db.session.add(comm)

                    db.session.commit()
                except Exception as e:
                    app_instance.logger.error(f"Erreur lors de l'enregistrement de la communication: {e}")
                    db.session.rollback()

        # Lancer l'enregistrement en base de façon asynchrone
        Thread(target=save_communication, args=(current_app._get_current_object(),)).start()

    except Exception as e:
        current_app.logger.error(f"Erreur lors du lancement de l'enregistrement: {e}")

    return success


def send_task_notification(task, event_type, user=None, additional_data=None, notify_all=False, mentioned_users=None):
    """
    Envoie une notification concernant une tâche

    :param task: La tâche concernée
    :param event_type: Type d'événement ('status_change', 'comment_added', 'comment_reply', 'time_logged')
    :param user: L'utilisateur qui a effectué l'action
    :param additional_data: Données supplémentaires (commentaire, temps, etc.)
    :param notify_all: Si True, notifie tous les participants
    :param mentioned_users: Liste des utilisateurs mentionnés dans le commentaire
    """
    # Vérifier l'environnement
    is_production = current_app.config.get("FLASK_ENV") == "production"

    # Déterminer les destinataires de façon optimisée
    recipients = set()  # Utiliser un set pour éviter les doublons

    # Pour les réponses aux commentaires, notifier spécifiquement l'auteur du commentaire parent
    if event_type == "comment_reply":
        parent_comment = additional_data.get("parent_comment")
        reply = additional_data.get("reply")
        if parent_comment and parent_comment.user:
            # Charger les préférences de notification de l'auteur du commentaire parent
            from sqlalchemy.orm import joinedload

            parent_author = User.query.options(joinedload(User.notification_preferences)).get(parent_comment.user_id)
            if parent_author and parent_author.notification_preferences:
                prefs = parent_author.notification_preferences
                if prefs.email_notifications_enabled and prefs.task_comment_added:
                    recipients.add(parent_author.email)

    if notify_all:
        # Optimiser les requêtes avec des jointures
        from sqlalchemy.orm import joinedload

        # Notifier l'utilisateur assigné à la tâche (s'il existe)
        if task.user_id:
            assigned_user = User.query.options(joinedload(User.notification_preferences)).get(task.user_id)
            if assigned_user and assigned_user.notification_preferences:
                prefs = assigned_user.notification_preferences
                if prefs.email_notifications_enabled:
                    if (
                        (event_type == "status_change" and prefs.task_status_change)
                        or (event_type == "comment_added" and prefs.task_comment_added)
                        or (event_type == "comment_reply" and prefs.task_comment_added)
                        or (event_type == "time_logged" and prefs.task_time_logged)
                        or (event_type == "task_created" and prefs.task_created)
                    ):
                        recipients.add(assigned_user.email)

        # En production seulement, notifier les clients du projet
        if is_production:
            # Une seule requête avec jointure pour tous les clients
            client_users = User.query.options(joinedload(User.notification_preferences)).filter_by(role="client").all()
            for client_user in client_users:
                if client_user.has_access_to_client(task.project.client_id):
                    if (
                        client_user.notification_preferences
                        and client_user.notification_preferences.email_notifications_enabled
                    ):
                        prefs = client_user.notification_preferences
                        if (
                            (event_type == "status_change" and prefs.task_status_change)
                            or (event_type == "comment_added" and prefs.task_comment_added)
                            or (event_type == "comment_reply" and prefs.task_comment_added)
                            or (event_type == "time_logged" and prefs.task_time_logged)
                            or (event_type == "task_created" and prefs.task_created)
                        ):
                            recipients.add(client_user.email)

    # Ajouter les utilisateurs mentionnés (optimisé)
    if mentioned_users:
        mentioned_ids = [u["id"] for u in mentioned_users]
        mentioned_users_objs = User.query.filter(User.id.in_(mentioned_ids)).all()
        for user_obj in mentioned_users_objs:
            if user_obj.email:
                recipients.add(user_obj.email)

    # Éviter d'envoyer à l'utilisateur qui a effectué l'action
    if user and user.email in recipients:
        recipients.remove(user.email)

    # Si aucun destinataire, sortir
    if not recipients:
        current_app.logger.info(f"Aucun destinataire pour la notification de tâche {task.id}")
        return

    # Préparer le contenu de l'email selon le type d'événement
    if event_type == "status_change":
        subject = f"[ChronoTrak] Statut de tâche modifié: {task.title}"
        old_status = additional_data.get("old_status", "inconnu")
        new_status = additional_data.get("new_status", task.status)

        # Construire l'URL de la tâche
        task_url = url_for("tasks.task_details", slug_or_id=task.slug, _external=True)

        # Préparer le contenu HTML
        html_content = render_template(
            "emails/task_notification.html",
            task=task,
            user=user,
            notification_type=event_type,
            old_status=old_status,
            new_status=new_status,
            url=task_url,
        )

        text = f"""
Bonjour,

La tâche "{task.title}" a changé de statut:

- Projet: {task.project.name}
- Client: {task.project.client.name}
- Ancien statut: {old_status}
- Nouveau statut: {new_status}
- Modifié par: {user.name if user else "Système"}

Voir la tâche: {task_url}

Ceci est un message automatique envoyé par ChronoTrak.
Pour ne plus recevoir ces notifications, modifiez vos préférences dans votre profil.
        """

    elif event_type == "comment_added":
        comment = additional_data.get("comment")
        if not comment:
            return

        subject = f"[ChronoTrak] Nouveau commentaire sur: {task.title}"

        # Construire l'URL de la tâche
        task_url = url_for("tasks.task_details", slug_or_id=task.slug, _external=True)

        # Préparer le contenu HTML
        html_content = render_template(
            "emails/task_notification.html",
            task=task,
            user=user,
            notification_type=event_type,
            comment=comment,
            url=task_url,
            mentioned_users=mentioned_users,
        )

        text = f"""
Bonjour,

Un nouveau commentaire a été ajouté sur la tâche "{task.title}":

- Projet: {task.project.name}
- Client: {task.project.client.name}
- Commentaire par: {user.name if user else "Système"}

{comment.content}

Voir la tâche: {task_url}

Ceci est un message automatique envoyé par ChronoTrak.
Pour ne plus recevoir ces notifications, modifiez vos préférences dans votre profil.
        """

    elif event_type == "comment_reply":
        reply = additional_data.get("reply")
        parent_comment = additional_data.get("parent_comment")
        if not reply or not parent_comment:
            return

        subject = f"[ChronoTrak] Réponse à votre commentaire sur: {task.title}"

        # Construire l'URL de la tâche
        task_url = url_for("tasks.task_details", slug_or_id=task.slug, _external=True)

        # Préparer le contenu HTML
        html_content = render_template(
            "emails/task_notification.html",
            task=task,
            user=user,
            notification_type=event_type,
            reply=reply,
            parent_comment=parent_comment,
            url=task_url,
            mentioned_users=mentioned_users,
        )

        text = f"""
Bonjour,

{user.name if user else "Quelqu'un"} a répondu à votre commentaire sur la tâche "{task.title}":

- Projet: {task.project.name}
- Client: {task.project.client.name}
- Votre commentaire: {parent_comment.content[:100]}{"..." if len(parent_comment.content) > 100 else ""}
- Réponse par: {user.name if user else "Système"}

{reply.content}

Voir la tâche: {task_url}

Ceci est un message automatique envoyé par ChronoTrak.
Pour ne plus recevoir ces notifications, modifiez vos préférences dans votre profil.
        """

    elif event_type == "time_logged":
        time_entry = additional_data.get("time_entry")
        if not time_entry:
            return

        subject = f"[ChronoTrak] Temps enregistré sur: {task.title}"

        # Construire l'URL de la tâche
        task_url = url_for("tasks.task_details", slug_or_id=task.slug, _external=True)

        # Formater la durée en minutes/h min
        formatted_time = format_time(time_entry.minutes)

        # Préparer le contenu HTML
        html_content = render_template(
            "emails/task_notification.html",
            task=task,
            user=user,
            notification_type=event_type,
            time_entry=time_entry,
            url=task_url,
        )

        text = f"""
Bonjour,

Du temps a été enregistré sur la tâche "{task.title}":

- Projet: {task.project.name}
- Client: {task.project.client.name}
- Temps: {formatted_time}
- Enregistré par: {user.name if user else "Système"}
- Description: {time_entry.description if time_entry.description else "N/A"}

Voir la tâche: {task_url}

Ceci est un message automatique envoyé par ChronoTrak.
Pour ne plus recevoir ces notifications, modifiez vos préférences dans votre profil.
        """

    elif event_type == "task_created":
        subject = f"[ChronoTrak] Nouvelle tâche assignée: {task.title}"
        # Construire l'URL de la tâche
        task_url = url_for("tasks.task_details", slug_or_id=task.slug, _external=True)
        html_content = render_template(
            "emails/task_notification.html", task=task, user=user, notification_type=event_type, url=task_url
        )
        text = f"""
Bonjour,

Une nouvelle tâche vous a été assignée : "{task.title}"

- Projet: {task.project.name}
- Client: {task.project.client.name}
- Créée par: {user.name if user else "Système"}

Voir la tâche: {task_url}

Ceci est un message automatique envoyé par ChronoTrak.
Pour ne plus recevoir ces notifications, modifiez vos préférences dans votre profil.
        """
    else:
        # Type d'événement non pris en charge
        current_app.logger.warning(f"Type d'événement non pris en charge: {event_type}")
        return

    # Envoyer l'email
    send_email(
        subject,
        recipients,
        text,
        html_content,
        email_type=f"task_{event_type}",
        task_id=task.id,
        project_id=task.project_id,
        triggered_by_id=user.id if user else None,
    )


def send_low_credit_notification(project):
    """
    Envoie une notification lorsque le crédit d'un projet devient faible

    :param project: Le projet dont le crédit est faible
    """
    # Trouver les utilisateurs à notifier
    recipients = []

    # Notifier les administrateurs
    admins = User.query.filter_by(role="admin").all()
    for admin in admins:
        if admin.notification_preferences and admin.notification_preferences.email_notifications_enabled:
            if admin.notification_preferences.project_credit_low:
                recipients.append(admin.email)

    # Notifier le client
    client_users = User.query.filter_by(role="client").all()
    for client_user in client_users:
        if client_user.has_access_to_client(project.client_id):
            if (
                client_user.notification_preferences
                and client_user.notification_preferences.email_notifications_enabled
            ):
                if client_user.notification_preferences.project_credit_low:
                    recipients.append(client_user.email)

    # Si aucun destinataire, sortir
    if not recipients:
        current_app.logger.info(f"Aucun destinataire pour l'alerte de crédit faible du projet {project.id}")
        return

    # Préparer le contenu de l'email
    subject = f"[ChronoTrak] ALERTE: Crédit faible pour le projet {project.name}"

    template = "emails/project_low_credit.html"
    html = render_template(
        template, project=project, url=url_for("projects.project_details", project_id=project.id, _external=True)
    )

    text = f"""
        Alerte de crédit faible pour le projet "{project.name}"

        Détails du projet:
        - Client: {project.client.name}
        - Crédit restant: {format_time(project.remaining_credit)}

        Veuillez prendre les mesures nécessaires pour éviter l'interruption du service.

        Voir le projet: {url_for("projects.project_details", project_id=project.id, _external=True)}
        """

    # Envoyer l'email
    send_email(subject, recipients, text, html, email_type="project_low_credit", project_id=project.id)


def send_password_reset_email(user, is_new_account=False):
    """
    Envoie un email de réinitialisation de mot de passe à l'utilisateur

    :param user: L'utilisateur auquel envoyer l'email
    :param is_new_account: True si c'est un nouveau compte, False pour une réinitialisation
    :return: True si l'email a été envoyé avec succès, False sinon
    """
    # Import ici pour éviter l'importation circulaire
    from app.models.token import PasswordResetToken

    # Vérifier si l'utilisateur existe
    if not user:
        current_app.logger.error("Tentative d'envoi d'email à un utilisateur inexistant")
        return False

    # Vérifier si l'utilisateur a un email
    if not user.email:
        current_app.logger.error(f"L'utilisateur {user.id} n'a pas d'email")
        return False

    # Créer un jeton de réinitialisation
    token = PasswordResetToken.generate_for_user(user.id)

    # Construire l'URL avec le jeton
    reset_url = url_for("auth.reset_password", token=token.token, _external=True)

    # Préparer le contenu de l'email
    if is_new_account:
        subject = "[ChronoTrak] Activation de votre compte"
    else:
        subject = "[ChronoTrak] Réinitialisation de votre mot de passe"

    template = "emails/password_reset.html"
    html = render_template(template, user=user, reset_url=reset_url, is_new_account=is_new_account)

    if is_new_account:
        text = f"""
Bonjour {user.name},

Un compte a été créé pour vous sur la plateforme ChronoTrak de gestion de crédit-temps.

Voici vos informations de connexion :
- Email : {user.email}
- Rôle : {user.role}

Pour définir votre mot de passe, veuillez cliquer sur le lien suivant :
{reset_url}

Important : Ce lien est valable pendant 24 heures.

Une fois votre mot de passe défini, vous pourrez vous connecter à la plateforme et accéder à vos projets et au suivi des temps.

Si vous n'êtes pas à l'origine de cette demande, veuillez ignorer cet email.

Ceci est un message automatique envoyé par ChronoTrak.
Pour toute question, veuillez contacter votre administrateur.
        """
    else:
        text = f"""
Bonjour {user.name},

Une demande de réinitialisation de mot de passe a été effectuée pour votre compte sur la plateforme ChronoTrak.

Voici vos informations de connexion :
- Email : {user.email}
- Rôle : {user.role}

Pour réinitialiser votre mot de passe, veuillez cliquer sur le lien suivant :
{reset_url}

Important : Ce lien est valable pendant 24 heures.

Si vous n'êtes pas à l'origine de cette demande, veuillez ignorer cet email.

Ceci est un message automatique envoyé par ChronoTrak.
Pour toute question, veuillez contacter votre administrateur.
        """

    try:
        # Envoyer l'email en utilisant la logique centralisée de send_email
        send_email(subject, [user.email], text, html, email_type="password_reset", user_id=user.id)
        current_app.logger.info(f"Email de réinitialisation envoyé à {user.email}")
        return True
    except Exception as e:
        current_app.logger.error(f"Erreur lors de l'envoi de l'email de réinitialisation: {e}")
        return False
