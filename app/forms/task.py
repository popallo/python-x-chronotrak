from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FloatField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from app.models.user import User

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
        super(TaskForm, self).__init__(*args, **kwargs)
        # Dynamiquement charger la liste des utilisateurs
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