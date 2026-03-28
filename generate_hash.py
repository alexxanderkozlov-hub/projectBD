from utils.hash import hash_password

password = "admin123"
hashed = hash_password(password)

print("HASH:", hashed)