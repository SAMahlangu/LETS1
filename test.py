from werkzeug.security import generate_password_hash, check_password_hash

# Hash a password
hashed_password = generate_password_hash("123")
print("Hashed Password:", hashed_password)

# Test password validation
print(check_password_hash(hashed_password, "123"))  # Should return True
print(check_password_hash(hashed_password, "wrongpassword"))  # Should return False
