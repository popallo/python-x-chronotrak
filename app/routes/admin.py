from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import mail, db
from flask_mail import Message
from app.forms.admin import TestEmailForm
from app.utils.decorators import login_and_admin_required
from app.utils.route_utils import save_to_db
from app.models.task import Task
from app.models.project import Project
from app.models.user import User
from sqlalchemy import or_

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

@admin.route('/tasks')
@login_and_admin_required
def list_tasks():
    # Récupération des paramètres de filtrage
    status = request.args.get('status')
    priority = request.args.get('priority')
    project_id = request.args.get('project_id', type=int)
    user_id = request.args.get('user_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Nombre de tâches par page

    # Construction de la requête de base
    query = Task.query.order_by(Task.created_at.desc())

    # Application des filtres
    if status:
        query = query.filter(Task.status == status)
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
    users = User.query.filter(User.role != 'client').order_by(User.name).all()

    return render_template('admin/tasks.html',
                         tasks=tasks,
                         projects=projects,
                         users=users,
                         title='Gestion des tâches')

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