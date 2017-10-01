from flask import Flask, request, render_template
from flask_login import LoginManager, login_user, logout_user, login_required, \
                        current_user
from flask_sqlalchemy import SQLAlchemy
from requests.auth import HTTPBasicAuth
import sys

sys.path.insert(0, "../tost-client")
import tostclient

from forms import SignupForm, LoginForm, CreateForm
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

    def get_auth():
        email = current_user.email
        auth_token = current_user.auth_token

        return {"auth": HTTPBasicAuth(email, auth_token)}
    
    def add_content(auth, ppgn_token="", data={}):
        auth["ppgn_token"] = ppgn_token
        auth["data"] = data

        return auth

    def resolve_argv(cmd, args):
        if cmd == "signup":
            if not validate_email(args[0]):
                return "invalid e-mail"
        
            return {"email": args[0]}
        
        elif cmd == "login":
            if not validate_auth_token(args[0]):
                return "invalid auth token"
    
            return {"auth_token": args[0]}

        auth = get_auth()

        if cmd == "list":
            return auth

        elif cmd == "create":
            data = {"body": args[0]}
            return add_content(auth, data=data)

    def compose_request(args, method, cmd):
        result, response = execute_request(client, args, method, cmd)

        if not result:
            return response

        if cmd == "login":
            email = response["data"]["email"]
            auth_token = response["data"]["auth_token"]

            user = User.query.filter_by(email=email).first()

            if not user:
                user = User(email, auth_token)
                user.save()

            login_user(user)

        if cmd == "list":
            result = []

            for k, v in response["data"]["tosts"].iteritems():
                result.append(k + ": " + v)

            return result

        return response["msg"]

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
            
            if isinstance(args, str):
                return args

            return compose_request(args, "start", cmd)

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
            
            if isinstance(args, str):
                return args

            return compose_request(args, "start", cmd)

    @app.route("/tost", methods=["GET", "POST"])
    @login_required
    def tost():
        form = CreateForm()
        if request.method == "GET":

            cmd = "list"
            args = resolve_argv(cmd, [])

            data = compose_request(args, "multiple", cmd)
            return render_template("create.html", form=form, data=data)

        if request.method == "POST":
            if not form.validate_on_submit():
                return "form did not validate"

            body = form.body.data

            cmd = "create"
            args = resolve_argv(cmd, [body])

            return compose_request(args, "individual", cmd)


    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return "logout successful"


    @login_manager.user_loader
    def load_user(email):
        return User.query.filter_by(email=email).first()

    return app
