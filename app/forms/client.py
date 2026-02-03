from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional


class ClientForm(FlaskForm):
    name = StringField("Nom du client", validators=[DataRequired(), Length(min=2, max=100)])
    contact_name = StringField("Nom du contact", validators=[Optional(), Length(max=100)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=120)])
    phone = StringField("Téléphone", validators=[Optional(), Length(max=20)])
    address = TextAreaField("Adresse", validators=[Optional(), Length(max=200)])
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Enregistrer")
