from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FloatField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from app.models.user import User
from app.models.client import Client

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
    estimated_time = FloatField('Temps estimé (heures)', validators=[Optional(), NumberRange(min=0.1)])
    user_id = SelectField('Assigné à', validators=[Optional()], coerce=int)
    submit = SubmitField('Enregistrer')
    
    def __init__(self, *args, **kwargs):
        # Extraire current_user des arguments
        current_user = kwargs.pop('current_user', None)
        
        # Appeler le constructeur parent
        super(TaskForm, self).__init__(*args, **kwargs)
        
        # Logique pour filtrer les utilisateurs
        if current_user and current_user.is_client():
            # Récupérer les IDs des clients auxquels l'utilisateur est rattaché
            client_ids = [client.id for client in current_user.clients]
            
            # Récupérer tous les utilisateurs clients qui sont rattachés aux mêmes clients
            client_users = User.query.filter(
                User.role == 'client',
                User.clients.any(Client.id.in_(client_ids))
            ).all()
            
            # Récupérer les IDs de ces utilisateurs
            client_user_ids = [user.id for user in client_users]
            
            # Récupérer tous les admins et techniciens
            other_users = User.query.filter(
                (User.role == 'admin') | (User.role == 'technicien')
            ).all()
            
            # Combiner les listes
            all_visible_users = client_users + other_users
            
            # Supprimer les doublons éventuels
            unique_users = []
            seen_ids = set()
            for user in all_visible_users:
                if user.id not in seen_ids:
                    unique_users.append(user)
                    seen_ids.add(user.id)
            
            # Trier par nom
            unique_users.sort(key=lambda x: x.name)
            
            # Définir les choix
            self.user_id.choices = [(0, '-- Non assigné --')] + [
                (user.id, user.name) for user in unique_users
            ]
        else:
            # Pour les admins et techniciens, montrer tous les utilisateurs
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
        # Créer des options par tranches de 15 minutes (0,25h) jusqu'à 8 heures
        # Format: (valeur, étiquette) où l'étiquette utilise une virgule
        hours_options = [(round(i * 0.25, 2), str(round(i * 0.25, 2)).replace('.', ',')) for i in range(1, 33)]
        self.hours.choices = hours_options

class CommentForm(FlaskForm):
    content = TextAreaField('Commentaire', validators=[DataRequired()])
    submit = SubmitField('Ajouter un commentaire')