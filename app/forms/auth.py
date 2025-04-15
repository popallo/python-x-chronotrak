from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models.user import User

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
    role = SelectField('Rôle', choices=[('technicien', 'Technicien'), ('admin', 'Administrateur')])
    submit = SubmitField('Créer le compte')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Cet email est déjà utilisé. Veuillez en choisir un autre.')

class ProfileForm(FlaskForm):
    name = StringField('Nom', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[Email()])  # En lecture seule dans le template
    password = PasswordField('Nouveau mot de passe', validators=[Length(min=8)])
    confirm_password = PasswordField('Confirmer le mot de passe', 
                                    validators=[EqualTo('password')])
    submit = SubmitField('Mettre à jour')