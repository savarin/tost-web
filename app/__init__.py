from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
import sys

sys.path.insert(0, "../tost-client")
import tostclient

from forms import SignupForm
from helpers import validate_email


db = SQLAlchemy()

base_domain = "http://localhost:5000"
client = tostclient.TostClient(base_domain)


def resolve_argv(cmd, args):
    if cmd == "signup":
        if not validate_email(args[0]):
            return False, "invalid e-mail"

        return True, {"email": args[0]}


def compose_request(args, method, cmd):
    try:
        exec("response = client.{}(args, cmd)".format(method))
    except Exception as e:
        return str(e)

    return response["msg"]


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

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        form = SignupForm()
        if request.method == "GET":
            return render_template("signup.html", form=form)
    
        elif request.method == "POST":
            if not form.validate_on_submit():
                return "form did not validate"

            cmd = "signup"
            email = form.email.data
            args = resolve_argv(cmd, [email])
            
            if not args[0]:
                return args[1]

            return compose_request(args[1], "start", cmd)

    return app
