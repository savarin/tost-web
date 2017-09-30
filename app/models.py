from __init__ import db


class User(db.Model):
    email = db.Column(db.String(32), primary_key=True)
    auth_token = db.Column(db.String(8), unique=True)

    def __init__(self, email, auth_token):
        self.email = email
        self.auth_token = auth_token

    def __repr__(self):
        return "<%s>" % self.email

    def get_id(self):
        return str(self.email)

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def save(self):
        db.session.add(self)
        db.session.commit()
