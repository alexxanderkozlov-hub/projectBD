from utils.hash import hash_password

password = "user123"
hashed = hash_password(password)

print("HASH:", hashed)