from flask_wtf import Form
from wtforms import StringField, SubmitField


class SignupForm(Form):
    email = StringField("email")
    submit = SubmitField("signup")


class LoginForm(Form):
    token = StringField("token")
    submit = SubmitField("login")    


class CreateForm(Form):
    body = StringField("body")
    submit = SubmitField("create")


class EditForm(Form):
    body = StringField("body")
    submit = SubmitField("edit")


class SwitchForm(Form):
    token = StringField("token")
    submit = SubmitField("upgrade")
