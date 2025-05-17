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
    
    def __init__(self, current_user=None, project=None, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        self.estimated_time.choices = [(0.0, "Non défini")] + generate_hour_options()
        
        # Récupérer tous les utilisateurs assignables
        assignable_users = []
        
        # Toujours inclure les administrateurs
        admins = User.query.filter_by(role='admin').all()
        assignable_users.extend(admins)
        
        # Toujours inclure les techniciens
        technicians = User.query.filter_by(role='technicien').all()
        assignable_users.extend(technicians)
        
        # Si un projet est fourni, inclure l'utilisateur client associé au client du projet
        if project and project.client:
            client_users = User.query.filter_by(role='client').all()
            for client_user in client_users:
                if client_user.has_access_to_client(project.client.id):
                    assignable_users.append(client_user)
                    break  # On ne prend que le premier utilisateur client trouvé
        
        # Créer la liste des choix en évitant les doublons
        seen_ids = set()
        choices = [(0, "Non assigné")]
        for user in assignable_users:
            if user.id not in seen_ids:
                seen_ids.add(user.id)
                choices.append((user.id, user.name))
        
        self.user_id.choices = choices

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