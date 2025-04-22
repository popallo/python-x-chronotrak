from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.models.client import Client
from app.forms.auth import LoginForm, RegistrationForm, ProfileForm
from app.models.task import Task, TimeEntry, Comment
from app.forms.auth import LoginForm, RegistrationForm, ProfileForm, UserEditForm

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('main.dashboard'))
        else:
            flash('Échec de la connexion. Vérifiez votre email et mot de passe.', 'danger')
    
    return render_template('auth/login.html', form=form, title='Connexion')

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    # Seuls les administrateurs peuvent créer de nouveaux comptes
    if not current_user.is_admin():
        flash('Accès refusé. Droits administrateur requis.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data,
            email=form.email.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        
        # Si l'utilisateur est un client, associer les clients sélectionnés
        if form.role.data == 'client' and form.clients.data:
            for client_id in form.clients.data:
                client = Client.query.get(client_id)
                if client:
                    user.clients.append(client)
        
        db.session.commit()
        flash(f'Compte créé pour {form.name.data}!', 'success')
        return redirect(url_for('auth.users'))
        
    return render_template('auth/register.html', form=form, title='Nouvel utilisateur')

@auth.route('/users')
@login_required
def users():
    # Seuls les administrateurs peuvent voir la liste des utilisateurs
    if not current_user.is_admin():
        flash('Accès refusé. Droits administrateur requis.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    users = User.query.all()
    return render_template('auth/users.html', users=users, title='Utilisateurs')

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        
        if form.password.data:
            current_user.set_password(form.password.data)
            
        db.session.commit()
        flash('Votre profil a été mis à jour!', 'success')
        return redirect(url_for('auth.profile'))
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.email.data = current_user.email
        
    return render_template('auth/profile.html', form=form, title='Mon profil')

@auth.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    # Vérifier les droits administrateur
    if not current_user.is_admin():
        flash('Accès refusé. Droits administrateur requis.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Empêcher l'admin de supprimer son propre compte
    if current_user.id == user_id:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'danger')
        return redirect(url_for('auth.users'))
    
    user = User.query.get_or_404(user_id)
    
    # Pour les utilisateurs de type client, vérifier s'ils sont liés à des tâches
    tasks_assigned = Task.query.filter_by(user_id=user.id).count()
    if tasks_assigned > 0:
        flash(f'Impossible de supprimer cet utilisateur car {tasks_assigned} tâche(s) lui sont assignées.', 'danger')
        return redirect(url_for('auth.users'))
    
    # Vérifier les entrées de temps
    time_entries = TimeEntry.query.filter_by(user_id=user.id).count()
    if time_entries > 0:
        flash(f'Impossible de supprimer cet utilisateur car {time_entries} entrée(s) de temps lui sont associées.', 'danger')
        return redirect(url_for('auth.users'))
    
    # Vérifier les commentaires
    comments = Comment.query.filter_by(user_id=user.id).count()
    if comments > 0:
        flash(f'Impossible de supprimer cet utilisateur car {comments} commentaire(s) lui sont associés.', 'danger')
        return redirect(url_for('auth.users'))
    
    # Si tout est OK, supprimer l'utilisateur
    db.session.delete(user)
    db.session.commit()
    flash(f'Utilisateur {user.name} supprimé avec succès!', 'success')
    return redirect(url_for('auth.users'))

@auth.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    # Vérifier les droits administrateur
    if not current_user.is_admin():
        flash('Accès refusé. Droits administrateur requis.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get_or_404(user_id)
    form = UserEditForm(original_email=user.email)
    
    if form.validate_on_submit():
        user.name = form.name.data
        user.email = form.email.data
        user.role = form.role.data
        
        # Gérer les associations client seulement si c'est un utilisateur de type client
        if form.role.data == 'client':
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
        flash(f'Utilisateur {user.name} mis à jour avec succès!', 'success')
        return redirect(url_for('auth.users'))
    
    elif request.method == 'GET':
        form.name.data = user.name
        form.email.data = user.email
        form.role.data = user.role
        # Pré-remplir les clients sélectionnés
        if user.role == 'client':
            form.clients.data = [client.id for client in user.clients]
    
    return render_template('auth/edit_user.html', form=form, user=user, title='Modifier utilisateur')