from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.models.client import Client
from app.forms.auth import LoginForm, RegistrationForm, ProfileForm

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