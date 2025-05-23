from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from app.models.user import User
from app.models.client import Client
from app.utils import get_client_choices

class UserForm(FlaskForm):
    """Formulaire utilisé uniquement pour le CSRF token dans la page des utilisateurs"""
    pass

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    remember = BooleanField('Se souvenir de moi')
    submit = SubmitField('Connexion')

class RegistrationForm(FlaskForm):
    name = StringField('Nom', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirmer le mot de passe', 
                                    validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Rôle', choices=[
        ('technicien', 'Technicien'), 
        ('admin', 'Administrateur'),
        ('client', 'Client')
    ])
    clients = SelectMultipleField('Clients associés (pour les utilisateurs de type client)', coerce=int)
    submit = SubmitField('Créer le compte')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Cet email est déjà utilisé. Veuillez en choisir un autre.')
    
    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.clients.choices = get_client_choices()

class ProfileForm(FlaskForm):
    name = StringField('Nom', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[Email()])  # En lecture seule dans le template
    password = PasswordField('Nouveau mot de passe', validators=[Length(min=8)])
    confirm_password = PasswordField('Confirmer le mot de passe', 
                                    validators=[EqualTo('password')])
    submit = SubmitField('Mettre à jour')

class UserEditForm(FlaskForm):
    name = StringField('Nom', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Rôle', choices=[
        ('technicien', 'Technicien'), 
        ('admin', 'Administrateur'),
        ('client', 'Client')
    ])
    clients = SelectMultipleField('Clients associés (pour les utilisateurs de type client)', coerce=int)
    password = PasswordField('Nouveau mot de passe', validators=[Optional(), Length(min=8)])
    confirm_password = PasswordField('Confirmer le mot de passe', 
                                    validators=[EqualTo('password')])
    submit = SubmitField('Mettre à jour')
    
    def __init__(self, *args, original_email=None, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        self.original_email = original_email
        self.clients.choices = get_client_choices()
    
    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Cet email est déjà utilisé. Veuillez en choisir un autre.')
            
class NotificationPreferenceForm(FlaskForm):
    email_notifications_enabled = BooleanField('Activer les notifications par email', default=True)
    task_status_change = BooleanField('Changements de statut des tâches', default=True)
    task_comment_added = BooleanField('Nouveaux commentaires', default=True)
    task_time_logged = BooleanField('Enregistrement de temps', default=True)
    project_credit_low = BooleanField('Alerte de crédit faible', default=True)
    submit = SubmitField('Enregistrer les préférences')

class PasswordResetForm(FlaskForm):
    password = PasswordField('Nouveau mot de passe', validators=[
        DataRequired(), 
        Length(min=8, message="Le mot de passe doit contenir au moins 8 caractères")
    ])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[
        DataRequired(), 
        EqualTo('password', message="Les mots de passe doivent correspondre")
    ])
    submit = SubmitField('Définir le mot de passe')

class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Demander la réinitialisation')