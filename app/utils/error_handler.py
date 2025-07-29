import traceback
from flask import current_app
from app.utils.email import send_email

def send_error_email(error, request_info=None):
    """
    Envoie un email aux administrateurs avec les détails de l'erreur.
    
    Args:
        error: L'exception qui a été levée
        request_info: Informations sur la requête qui a causé l'erreur
    """
    current_app.logger.info("Tentative d'envoi d'email d'erreur...")
    
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

        # Utiliser la logique centralisée de send_email
        # Les emails d'erreur vont automatiquement aux administrateurs selon les règles
        admin_email = current_app.config.get('ADMIN_EMAIL')
        current_app.logger.info(f"ADMIN_EMAIL configuré: {admin_email}")
        
        if admin_email:
            current_app.logger.info(f"Envoi de l'email d'erreur à {admin_email}")
            send_email(subject, [admin_email], body, body, email_type='error')
            current_app.logger.info("Email d'erreur envoyé avec succès")
        else:
            current_app.logger.warning("ADMIN_EMAIL non configuré, email d'erreur non envoyé")
            
    except Exception as e:
        current_app.logger.error(f"Échec de l'envoi de l'email d'erreur: {str(e)}")
        current_app.logger.error(f"Traceback: {traceback.format_exc()}") 