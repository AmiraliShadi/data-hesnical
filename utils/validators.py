def transform_email(email):
    return f'{email.split("@")[0]}-{email.split("@")[1].split(".")[0]}'
