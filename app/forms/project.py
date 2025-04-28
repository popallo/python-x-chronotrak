from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

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
        # Créer des options par tranches de 5 minutes jusqu'à 8 heures
        hours_options = []
        
        # Ajouter les options de 5 minutes à 1 heure par incréments de 5 minutes
        for i in range(1, 13):  # De 5 à 60 minutes par pas de 5
            minutes = i * 5
            decimal_value = round(minutes / 60, 2)
            
            if minutes < 60:
                label = f"{minutes} min"
            else:
                label = "1h"
            
            hours_options.append((decimal_value, label))
        
        # Ajouter les options de 1h15 à 8h par incréments de 15 minutes
        for i in range(5, 32):  # De 1h15 à 8h par pas de 15 minutes
            hour = i // 4
            minute = (i % 4) * 15
            decimal_value = round(hour + minute / 60, 2)
            
            if minute > 0:
                label = f"{hour}h {minute}min"
            else:
                label = f"{hour}h"
            
            hours_options.append((decimal_value, label))
        
        # Ajouter des options pour des grands blocs de temps (10h, 20h, 50h, 100h)
        additional_options = [(10.0, "10h"), (20.0, "20h"), (50.0, "50h"), (100.0, "100h")]
        hours_options.extend(additional_options)
        
        self.amount.choices = hours_options