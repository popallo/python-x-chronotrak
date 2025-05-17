from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FloatField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from app.models.user import User
from app.models.client import Client
from app.utils.time_format import generate_hour_options

class TaskForm(FlaskForm):
    title = StringField('Titre', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    status = SelectField('Statut', choices=[
        ('à faire', 'À faire'),
        ('en cours', 'En cours'),
        ('terminé', 'Terminé')
    ], validators=[DataRequired()])
    priority = SelectField('Priorité', choices=[
        ('basse', 'Basse'),
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('urgente', 'Urgente')
    ], validators=[DataRequired()])
    estimated_time = SelectField('Temps estimé', coerce=float, validators=[Optional()])
    user_id = SelectField('Assigné à', coerce=int, validators=[Optional()])
    submit = SubmitField('Enregistrer')
    
    def __init__(self, current_user=None, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        self.estimated_time.choices = [(0.0, "Non défini")] + generate_hour_options()
        
        # Si l'utilisateur est un client, on ne montre que les techniciens de son client
        if current_user and current_user.is_client():
            self.user_id.choices = [(0, "Non assigné")] + [
                (user.id, user.name) 
                for user in current_user.client.technicians
            ]
        else:
            # Pour les administrateurs et techniciens, on montre tous les techniciens
            self.user_id.choices = [(0, "Non assigné")] + [
                (user.id, user.name) 
                for user in User.query.filter_by(role='technician').all()
            ]

class TimeEntryForm(FlaskForm):
    hours = SelectField('Heures', coerce=float, validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Enregistrer')
    
    def __init__(self, *args, **kwargs):
        super(TimeEntryForm, self).__init__(*args, **kwargs)
        self.hours.choices = generate_hour_options()

class CommentForm(FlaskForm):
    content = TextAreaField('Commentaire', validators=[DataRequired(), Length(min=1, max=1000)])
    submit = SubmitField('Publier')

class EditCommentForm(FlaskForm):
    content = TextAreaField('Commentaire', validators=[DataRequired(), Length(min=1, max=1000)])
    submit = SubmitField('Modifier')

class DeleteTaskForm(FlaskForm):
    submit = SubmitField('Supprimer')