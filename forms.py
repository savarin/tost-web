from flask_wtf import Form
from wtforms import StringField, SubmitField


class SignupForm(Form):
    email = StringField("email")
    submit = SubmitField("signup")
