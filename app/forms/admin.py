from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, NumberRange
from app.models.project import Project

class TestEmailForm(FlaskForm):
    recipient = StringField('Destinataire', validators=[DataRequired(), Email()])
    subject = StringField('Sujet', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Envoyer')

class TimeTransferForm(FlaskForm):
    source_project_id = SelectField('Projet source', coerce=int, validators=[DataRequired()])
    target_project_id = SelectField('Projet destination', coerce=int, validators=[DataRequired()])
    amount = FloatField('Montant (heures)', validators=[
        DataRequired(),
        NumberRange(min=0.1, message="Le montant doit être supérieur à 0")
    ])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Transférer le temps')

    def __init__(self, *args, **kwargs):
        super(TimeTransferForm, self).__init__(*args, **kwargs)
        # Les projets seront chargés dynamiquement dans la route