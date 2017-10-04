import re
from uuid import uuid4


def validate_email(email):
    if not (len(email.split("@")) == 2 and
            len(email.split("@")[-1].split(".")) >= 2):
        return False
    return True


def validate_auth_token(auth_token):
    if not (len(auth_token) == 8 and
            re.match("^[a-f0-9]*$", auth_token)):
        return False
    return True


def create_token(length):
    return uuid4().hex[:length]
