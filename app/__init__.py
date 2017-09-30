from flask import Flask, request, render_template
from flask_login import LoginManager, login_user
from flask_sqlalchemy import SQLAlchemy
import sys

sys.path.insert(0, "../tost-client")
import tostclient

from forms import SignupForm, LoginForm
from helpers import validate_email, validate_auth_token


db = SQLAlchemy()


def execute_request(client, args, method, cmd):
    try:
        exec("response = client.{}(args, cmd)".format(method))
    except Exception as e:
        return False, str(e)

    return True, response


def create_app():
    from models import User

    app = Flask(__name__)
    app.secret_key = "a1b2c3d4"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/client.db"
    app.debug = True

    db.init_app(app)
    with app.app_context():
        db.create_all()
        db.session.commit()

    login_manager = LoginManager()
    login_manager.init_app(app)

    base_domain = "http://localhost:5000"
    client = tostclient.TostClient(base_domain)

    def resolve_argv(cmd, args):
        if cmd == "signup":
            if not validate_email(args[0]):
                return False, "invalid e-mail"
        
            return True, {"email": args[0]}
        
        elif cmd == "login":
            if not validate_auth_token(args[0]):
                return False, "invalid auth token"
    
            return True, {"auth_token": args[0]}

    def compose_request(args, method, cmd):
        response = execute_request(client, args, method, cmd)

        if not response[0]:
            return response[1]

        if cmd == "login":
            user = User(args["email"], args["auth_token"])
            user.save()

            login_user(user)

        return response[1]["msg"]

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        form = SignupForm()
        if request.method == "GET":
            return render_template("signup.html", form=form)
    
        elif request.method == "POST":
            if not form.validate_on_submit():
                return "form did not validate"

            email = form.email.data

            cmd = "signup"
            args = resolve_argv(cmd, [email])
            
            if not args[0]:
                return args[1]

            return compose_request(args[1], "start", cmd)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        form = LoginForm()
        if request.method == "GET":
            return render_template("login.html", form=form)
    
        elif request.method == "POST":
            if not form.validate_on_submit():
                return "form did not validate"

            auth_token = form.token.data

            cmd = "login"
            args = resolve_argv(cmd, [auth_token])
            
            if not args[0]:
                return args[1]

            email = form.email.data
            args[1]["email"] = email

            return compose_request(args[1], "start", cmd)

    @login_manager.user_loader
    def load_user(email):
        return User.query.filter_by(email=email).first()

    return app
