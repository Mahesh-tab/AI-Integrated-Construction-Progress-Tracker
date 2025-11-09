import bcrypt

def verify_password(plain_password, hashed_password):
    """Verifies a plain password against a hashed one."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)
