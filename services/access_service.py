def is_admin(user):
    return user["role"] == "admin"

def is_user(user):
    return user["role"] == "user"