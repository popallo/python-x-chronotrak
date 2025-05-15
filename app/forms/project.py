from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, SubmitField, SelectField, HiddenField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from app.utils.time_format import generate_hour_options

class ProjectForm(FlaskForm):
    name = StringField('Nom du projet', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    initial_credit = FloatField('Crédit initial (heures)', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Enregistrer')

class AddCreditForm(FlaskForm):
    amount = SelectField('Heures à ajouter', validators=[DataRequired()], coerce=float)
    note = StringField('Note', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Ajouter le crédit')
    
    def __init__(self, *args, **kwargs):
        super(AddCreditForm, self).__init__(*args, **kwargs)
        self.amount.choices = generate_hour_options(
            extra_blocks=[(10.0, "10h"), (20.0, "20h"), (50.0, "50h"), (100.0, "100h")]
        )

class DeleteProjectForm(FlaskForm):
    submit = SubmitField('Supprimer')