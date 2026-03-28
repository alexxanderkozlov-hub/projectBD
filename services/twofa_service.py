import random

codes = {}

def generate_code(user_id):
    code = str(random.randint(100000, 999999))
    codes[user_id] = code
    print("2FA CODE:", code)
    return code

def verify_code(user_id, code):
    return codes.get(user_id) == code