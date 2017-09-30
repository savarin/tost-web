

def validate_email(email):
    if not (len(email.split("@")) == 2 and
            len(email.split("@")[-1].split(".")) >= 2):
        return False
    return True
