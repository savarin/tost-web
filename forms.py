from flask_wtf import Form
from wtforms import StringField, SubmitField


class SignupForm(Form):
    email = StringField("email")
    submit = SubmitField("signup")


class LoginForm(Form):
    email = StringField("email")
    token = StringField("token")
    submit = SubmitField("login")    


class CreateForm(Form):
    tost = StringField("tost")
    submit = SubmitField("create")