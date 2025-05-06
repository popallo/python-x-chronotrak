import traceback
from flask import current_app
from flask_mail import Message
from app import mail

def send_error_email(error, request_info=None):
    """
    Envoie un email aux administrateurs avec les détails de l'erreur.
    
    Args:
        error: L'exception qui a été levée
        request_info: Informations sur la requête qui a causé l'erreur
    """
    if not current_app.config.get('MAIL_SERVER'):
        current_app.logger.error("Configuration email manquante pour l'envoi des erreurs")
        return

    try:
        subject = f"[ChronoTrak] Erreur serveur: {type(error).__name__}"
        
        # Préparation du corps du message
        body = f"""
Une erreur s'est produite sur ChronoTrak:

Type d'erreur: {type(error).__name__}
Message d'erreur: {str(error)}

Stack trace:
{traceback.format_exc()}
"""

        if request_info:
            body += f"""
Informations sur la requête:
URL: {request_info.get('url', 'N/A')}
Méthode: {request_info.get('method', 'N/A')}
IP: {request_info.get('ip', 'N/A')}
User Agent: {request_info.get('user_agent', 'N/A')}
"""

        msg = Message(
            subject=subject,
            recipients=[current_app.config['ADMIN_EMAIL']],
            body=body
        )
        
        mail.send(msg)
        current_app.logger.info("Email d'erreur envoyé avec succès")
    except Exception as e:
        current_app.logger.error(f"Échec de l'envoi de l'email d'erreur: {str(e)}") 