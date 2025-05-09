from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, NumberRange, Length
from app.models.project import Project
from app.utils.time_format import generate_hour_options

class TestEmailForm(FlaskForm):
    recipient = StringField('Destinataire', validators=[DataRequired(), Email()])
    subject = StringField('Sujet', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Envoyer')

class TimeTransferForm(FlaskForm):
    source_project_id = SelectField('Projet source', coerce=int, validators=[DataRequired()])
    target_project_id = SelectField('Projet destination', coerce=int, validators=[DataRequired()])
    amount = SelectField('Montant (heures)', validators=[DataRequired()], coerce=float)
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Transférer le temps')

    def __init__(self, *args, **kwargs):
        super(TimeTransferForm, self).__init__(*args, **kwargs)
        # Les projets seront chargés dynamiquement dans la route
        self.amount.choices = generate_hour_options(
            extra_blocks=[(10.0, "10h"), (20.0, "20h"), (50.0, "50h"), (100.0, "100h")]
        )