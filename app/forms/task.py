from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FloatField, SubmitField
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
    ])
    priority = SelectField('Priorité', choices=[
        ('basse', 'Basse'),
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('urgente', 'Urgente')
    ], default='normale')
    # Utiliser une valeur vide comme chaîne au lieu de None
    estimated_time = SelectField('Temps estimé (heures)', validators=[Optional()], coerce=float)
    user_id = SelectField('Assigné à', validators=[Optional()], coerce=int)
    submit = SubmitField('Enregistrer')
    
    def __init__(self, *args, **kwargs):
        # Extraire current_user des arguments
        current_user = kwargs.pop('current_user', None)
        
        # Appeler le constructeur parent
        super(TaskForm, self).__init__(*args, **kwargs)
        
        self.estimated_time.choices = generate_hour_options(
            extra_blocks=[(10.0, "10h"), (15.0, "15h"), (20.0, "20h"), (40.0, "40h")],
            include_undefined=True
        )
        
        # Logique pour filtrer les utilisateurs (reste inchangée)
        if current_user and current_user.is_client():
            client_ids = [client.id for client in current_user.clients]
            
            client_users = User.query.filter(
                User.role == 'client',
                User.clients.any(Client.id.in_(client_ids))
            ).all()
            
            client_user_ids = [user.id for user in client_users]
            
            other_users = User.query.filter(
                (User.role == 'admin') | (User.role == 'technicien')
            ).all()
            
            all_visible_users = client_users + other_users
            
            unique_users = []
            seen_ids = set()
            for user in all_visible_users:
                if user.id not in seen_ids:
                    unique_users.append(user)
                    seen_ids.add(user.id)
            
            unique_users.sort(key=lambda x: x.name)
            
            self.user_id.choices = [(0, '-- Non assigné --')] + [
                (user.id, user.name) for user in unique_users
            ]
        else:
            self.user_id.choices = [(0, '-- Non assigné --')] + [
                (user.id, user.name) for user in User.query.order_by(User.name).all()
            ]

class TimeEntryForm(FlaskForm):
    # Remplacer FloatField par SelectField
    hours = SelectField('Heures passées', validators=[DataRequired()], coerce=float)
    description = TextAreaField('Description du travail effectué', validators=[Optional()])
    submit = SubmitField('Enregistrer le temps')
    
    def __init__(self, *args, **kwargs):
        super(TimeEntryForm, self).__init__(*args, **kwargs)
        self.hours.choices = generate_hour_options()

class CommentForm(FlaskForm):
    content = TextAreaField('Commentaire', validators=[DataRequired()])
    submit = SubmitField('Ajouter')

class EditCommentForm(FlaskForm):
    content = TextAreaField('Commentaire', validators=[DataRequired()])
    submit = SubmitField('Enregistrer')