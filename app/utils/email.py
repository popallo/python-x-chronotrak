from flask import render_template, current_app, url_for
from flask_mail import Message
from app import mail
from threading import Thread
from app.models.notification import NotificationPreference
from app.models.user import User

def send_async_email(app, msg):
    """Envoie un email de façon asynchrone"""
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, text_body, html_body, sender=None):
    """Envoie un email aux destinataires spécifiés"""
    if not current_app.config.get('MAIL_SERVER'):
        current_app.logger.warning("Configuration SMTP manquante - email non envoyé")
        return
    
    msg = Message(subject, recipients=recipients, 
                  sender=sender or current_app.config['MAIL_DEFAULT_SENDER'])
    msg.body = text_body
    msg.html = html_body
    
    # Envoyer de façon asynchrone pour ne pas bloquer l'application
    Thread(target=send_async_email, 
           args=(current_app._get_current_object(), msg)).start()

def send_task_notification(task, event_type, user=None, additional_data=None):
    """
    Envoie une notification concernant une tâche
    
    :param task: La tâche concernée
    :param event_type: Type d'événement ('status_change', 'comment_added', 'time_logged')
    :param user: L'utilisateur qui a effectué l'action
    :param additional_data: Données supplémentaires (commentaire, temps, etc.)
    """
    # Déterminer les destinataires
    recipients = []
    
    # Toujours notifier l'utilisateur assigné à la tâche (s'il existe)
    if task.user_id:
        assigned_user = User.query.get(task.user_id)
        if assigned_user and assigned_user.notification_preferences:
            prefs = assigned_user.notification_preferences
            if prefs.email_notifications_enabled:
                if (event_type == 'status_change' and prefs.task_status_change) or \
                   (event_type == 'comment_added' and prefs.task_comment_added) or \
                   (event_type == 'time_logged' and prefs.task_time_logged):
                    recipients.append(assigned_user.email)
    
    # Notifier le client (si applicable)
    # Nous devons trouver les utilisateurs de type client associés au client de ce projet
    client_users = User.query.filter_by(role='client').all()
    for client_user in client_users:
        if client_user.has_access_to_client(task.project.client_id):
            if client_user.notification_preferences and client_user.notification_preferences.email_notifications_enabled:
                prefs = client_user.notification_preferences
                if (event_type == 'status_change' and prefs.task_status_change) or \
                   (event_type == 'comment_added' and prefs.task_comment_added) or \
                   (event_type == 'time_logged' and prefs.task_time_logged):
                    recipients.append(client_user.email)
    
    # Éviter d'envoyer à l'utilisateur qui a effectué l'action
    if user and user.email in recipients:
        recipients.remove(user.email)
    
    # Si aucun destinataire, sortir
    if not recipients:
        current_app.logger.info(f"Aucun destinataire pour la notification de tâche {task.id}")
        return
    
    # Préparer le contenu de l'email selon le type d'événement
    if event_type == 'status_change':
        subject = f"[ChronoTrak] Statut de tâche modifié: {task.title}"
        old_status = additional_data.get('old_status', 'inconnu')
        new_status = additional_data.get('new_status', task.status)
        
        template = 'emails/task_status_changed.html'
        html = render_template(template, 
                              task=task, 
                              user=user,
                              old_status=old_status,
                              new_status=new_status,
                              url=url_for('tasks.task_details', task_id=task.id, _external=True))
        
        text = f"""
Bonjour,

La tâche "{task.title}" a changé de statut:

- Projet: {task.project.name}
- Client: {task.project.client.name}
- Ancien statut: {old_status}
- Nouveau statut: {new_status}
- Modifié par: {user.name if user else 'Système'}

Voir la tâche: {url_for('tasks.task_details', task_id=task.id, _external=True)}

Ceci est un message automatique envoyé par ChronoTrak.
Pour ne plus recevoir ces notifications, modifiez vos préférences dans votre profil.
        """
    
    elif event_type == 'comment_added':
        comment = additional_data.get('comment')
        if not comment:
            return
            
        subject = f"[ChronoTrak] Nouveau commentaire sur: {task.title}"
        
        template = 'emails/task_comment_added.html'
        html = render_template(template, 
                              task=task, 
                              user=user,
                              comment=comment,
                              url=url_for('tasks.task_details', task_id=task.id, _external=True))
        
        text = f"""
Bonjour,

Un nouveau commentaire a été ajouté sur la tâche "{task.title}":

- Projet: {task.project.name}
- Client: {task.project.client.name}
- Commentaire par: {user.name if user else 'Système'}

{comment.safe_content}

Voir la tâche: {url_for('tasks.task_details', task_id=task.id, _external=True)}

Ceci est un message automatique envoyé par ChronoTrak.
Pour ne plus recevoir ces notifications, modifiez vos préférences dans votre profil.
        """
    
    elif event_type == 'time_logged':
        time_entry = additional_data.get('time_entry')
        if not time_entry:
            return
            
        subject = f"[ChronoTrak] Temps enregistré sur: {task.title}"
        
        template = 'emails/task_time_logged.html'
        html = render_template(template, 
                              task=task, 
                              user=user,
                              time_entry=time_entry,
                              url=url_for('tasks.task_details', task_id=task.id, _external=True))
        
        text = f"""
Bonjour,

Du temps a été enregistré sur la tâche "{task.title}":

- Projet: {task.project.name}
- Client: {task.project.client.name}
- Temps: {time_entry.hours} heures
- Enregistré par: {user.name if user else 'Système'}
- Description: {time_entry.description if time_entry.description else 'N/A'}

Voir la tâche: {url_for('tasks.task_details', task_id=task.id, _external=True)}

Ceci est un message automatique envoyé par ChronoTrak.
Pour ne plus recevoir ces notifications, modifiez vos préférences dans votre profil.
        """
    
    else:
        # Type d'événement non pris en charge
        current_app.logger.warning(f"Type d'événement non pris en charge: {event_type}")
        return
    
    # Envoyer l'email
    send_email(subject, recipients, text, html)

def send_low_credit_notification(project):
    """
    Envoie une notification lorsque le crédit d'un projet devient faible
    
    :param project: Le projet dont le crédit est faible
    """
    # Trouver les utilisateurs à notifier
    recipients = []
    
    # Notifier les administrateurs
    admins = User.query.filter_by(role='admin').all()
    for admin in admins:
        if admin.notification_preferences and admin.notification_preferences.email_notifications_enabled:
            if admin.notification_preferences.project_credit_low:
                recipients.append(admin.email)
    
    # Notifier le client
    client_users = User.query.filter_by(role='client').all()
    for client_user in client_users:
        if client_user.has_access_to_client(project.client_id):
            if client_user.notification_preferences and client_user.notification_preferences.email_notifications_enabled:
                if client_user.notification_preferences.project_credit_low:
                    recipients.append(client_user.email)
    
    # Si aucun destinataire, sortir
    if not recipients:
        current_app.logger.info(f"Aucun destinataire pour l'alerte de crédit faible du projet {project.id}")
        return
    
    # Préparer le contenu de l'email
    subject = f"[ChronoTrak] ALERTE: Crédit faible pour le projet {project.name}"
    
    template = 'emails/project_low_credit.html'
    html = render_template(template, 
                          project=project,
                          url=url_for('projects.project_details', project_id=project.id, _external=True))
    
    text = f"""
ALERTE: Crédit de projet faible

Le crédit du projet "{project.name}" est très bas!

- Client: {project.client.name}
- Crédit restant: {project.remaining_credit} heures
- Crédit initial: {project.initial_credit} heures

Veuillez prendre les mesures nécessaires pour éviter l'interruption du service.

Voir le projet: {url_for('projects.project_details', project_id=project.id, _external=True)}

Ceci est un message automatique envoyé par ChronoTrak.
Pour ne plus recevoir ces notifications, modifiez vos préférences dans votre profil.
    """
    
    # Envoyer l'email
    send_email(subject, recipients, text, html)
    
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
    reset_url = url_for('auth.reset_password', token=token.token, _external=True)
    
    # Préparer le contenu de l'email
    if is_new_account:
        subject = f"[ChronoTrak] Activation de votre compte"
    else:
        subject = f"[ChronoTrak] Réinitialisation de votre mot de passe"
    
    template = 'emails/password_reset.html'
    html = render_template(template, 
                          user=user,
                          reset_url=reset_url,
                          is_new_account=is_new_account)
    
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
        # Déterminer les destinataires
        if current_app.config.get('FLASK_ENV') == 'development':
            # En développement, rediriger tous les emails vers l'admin
            admin_email = current_app.config.get('ADMIN_EMAIL')
            if admin_email:
                # Ajouter des infos pour identifier le destinataire initial
                subject = f"[DEV] {subject} (pour {user.email})"
                recipients = [admin_email]
            else:
                # Utiliser l'email de l'utilisateur en absence d'admin configuré
                recipients = [user.email]
        else:
            # En production, envoyer à l'utilisateur concerné
            recipients = [user.email]
        
        # Envoyer l'email
        send_email(subject, recipients, text, html)
        current_app.logger.info(f"Email de réinitialisation envoyé à {recipients}")
        return True
    except Exception as e:
        current_app.logger.error(f"Erreur lors de l'envoi de l'email de réinitialisation: {e}")
        return False