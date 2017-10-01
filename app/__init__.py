from flask import Flask, request, render_template
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from requests.auth import HTTPBasicAuth
import sys

sys.path.insert(0, "../tost-client")
import tostclient

from forms import SignupForm, LoginForm, CreateForm, EditForm, UpgradeForm, DisableForm
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

        ppgn_token = args[0]

        if cmd in set(["view", "access"]):
            return add_content(auth, ppgn_token=ppgn_token)

        elif cmd == "edit":
            data = {"body": args[1]}
            return add_content(auth, ppgn_token=ppgn_token, data=data)

        elif cmd in set(["upgrade", "disable"]):
            data = {"src-access-token": args[1]}
            return add_content(auth, ppgn_token=ppgn_token, data=data)

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

        elif cmd == "list":
            result = []
            for k, v in response["data"]["tosts"].iteritems():
                result.append(k + ": " + v)
            return result

        elif cmd == "view":
            access_token = response["data"]["tost"]["access-token"]
            body = response["data"]["tost"]["body"]
            return (access_token + ": " + body)

        elif cmd == "access":
            result = []
            for k, v in response["data"]["propagations"].iteritems():
                result.append(v["access-token"] + ": " + k)
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
            return str(data)

            return render_template("create.html", form=form, data=data)

        elif request.method == "POST":
            if not form.validate_on_submit():
                return "form did not validate"

            body = form.body.data

            cmd = "create"
            args = resolve_argv(cmd, [body])

            return compose_request(args, "individual", cmd)

    @app.route("/tost/<access_token>", methods=["GET", "POST"])
    @login_required
    def view_tost(access_token):
        form = EditForm()

        if request.method == "GET":
            cmd = "view"
            args = resolve_argv(cmd, [access_token])

            data = compose_request(args, "individual", cmd)
            return render_template("edit.html", form=form, data=data,
                    access_token=access_token)

        elif request.method == "POST":
            if not form.validate_on_submit():
                return "form did not validate"

            body = form.body.data

            cmd = "edit"
            args = resolve_argv(cmd, [access_token, body])

            return compose_request(args, "individual", cmd)

    @app.route("/tost/<access_token>/propagation", methods=["GET"])
    @login_required
    def propagation(access_token):
        cmd = "access"
        args = resolve_argv(cmd, [access_token])

        result = ""

        for item in compose_request(args, "permit", cmd):
            result += item + "<br>"

        return result

    @app.route("/tost/<access_token>/propagation/upgrade", methods=["GET", "POST"])
    @login_required
    def upgrade_propagation(access_token):
        form = UpgradeForm()

        if request.method == "GET":
            return render_template("upgrade.html", form=form,
                    access_token=access_token)

        elif request.method == "POST":
            if not form.validate_on_submit():
                return "form did not validate"

            token = form.token.data

            cmd = "upgrade"
            args = resolve_argv(cmd, [access_token, token])

            return compose_request(args, "switch", cmd)

    @app.route("/tost/<access_token>/propagation/disable", methods=["GET", "POST"])
    @login_required
    def disable_propagation(access_token):
        form = DisableForm()
        
        if request.method == "GET":
            return render_template("disable.html", form=form,
                    access_token=access_token)

        elif request.method == "POST":
            if not form.validate_on_submit():
                return "form did not validate"

            token = form.token.data

            cmd = "disable"
            args = resolve_argv(cmd, [access_token, token])

            return compose_request(args, "switch", cmd)

    @app.route("/current")
    @login_required
    def current():
        return str(current_user.email)

    @login_manager.user_loader
    def load_user(email):
        return User.query.filter_by(email=email).first()

    return app
