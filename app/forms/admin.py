from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email

class TestEmailForm(FlaskForm):
    recipient = StringField('Adresse email de test', validators=[DataRequired(), Email()])
    submit = SubmitField('Envoyer un email de test')