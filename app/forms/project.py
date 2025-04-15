from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class ProjectForm(FlaskForm):
    name = StringField('Nom du projet', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    initial_credit = FloatField('Crédit initial (heures)', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Enregistrer')

class AddCreditForm(FlaskForm):
    amount = FloatField('Heures à ajouter', validators=[DataRequired(), NumberRange(min=0.1)])
    note = StringField('Note', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Ajouter le crédit')