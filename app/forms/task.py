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
    hours = FloatField('Heures passées', validators=[DataRequired(), NumberRange(min=0.1)])
    description = TextAreaField('Description du travail effectué', validators=[Optional()])
    submit = SubmitField('Enregistrer le temps')

class CommentForm(FlaskForm):
    content = TextAreaField('Commentaire', validators=[DataRequired()])
    submit = SubmitField('Ajouter un commentaire')