from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import mail
from flask_mail import Message
from app.forms.admin import TestEmailForm
from app.utils.decorators import login_and_admin_required
from app.utils.route_utils import save_to_db

admin = Blueprint('admin', __name__, url_prefix='/admin')

@admin.before_request
def require_admin():
    if not current_user.is_authenticated or not current_user.is_admin():
        flash('Accès refusé. Droits administrateur requis.', 'danger')
        return redirect(url_for('main.dashboard'))

def send_test_email(recipient):
    """Envoie un email de test à l'adresse spécifiée"""
    try:
        msg = Message(
            subject="ChronoTrak - Test de configuration SMTP",
            recipients=[recipient],
            body="Ceci est un email de test envoyé depuis ChronoTrak. Si vous recevez cet email, la configuration SMTP fonctionne correctement.",
            html="<h1>ChronoTrak - Test de configuration SMTP</h1><p>Ceci est un email de test envoyé depuis ChronoTrak. Si vous recevez cet email, la configuration SMTP fonctionne correctement.</p>"
        )
        mail.send(msg)
        return True, None
    except Exception as e:
        return False, str(e)

@admin.route('/test-email', methods=['GET', 'POST'])
@login_and_admin_required
def test_email():
    form = TestEmailForm()
    
    if form.validate_on_submit():
        success, error = send_test_email(form.recipient.data)
        if success:
            flash(f'Email de test envoyé à {form.recipient.data}. Vérifiez votre boîte de réception.', 'success')
        else:
            flash(f'Erreur lors de l\'envoi de l\'email: {error}', 'danger')
        return redirect(url_for('admin.test_email'))
    
    # Récupérer la configuration SMTP pour l'afficher
    smtp_config = {
        'MAIL_SERVER': current_app.config.get('MAIL_SERVER'),
        'MAIL_PORT': current_app.config.get('MAIL_PORT'),
        'MAIL_USE_TLS': current_app.config.get('MAIL_USE_TLS'),
        'MAIL_USE_SSL': current_app.config.get('MAIL_USE_SSL'),
        'MAIL_USERNAME': current_app.config.get('MAIL_USERNAME'),
        'MAIL_DEFAULT_SENDER': current_app.config.get('MAIL_DEFAULT_SENDER')
    }
    
    return render_template('admin/test_email.html', 
                         form=form, 
                         config=smtp_config, 
                         title='Test SMTP')