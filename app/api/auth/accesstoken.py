from datetime import datetime, timedelta

import jwt

secret_key = "drive_sync_secret_key"

def create_access_token(username: str, expires_delta: timedelta):
    expire = datetime.utcnow() + expires_delta
    to_encode = {"sub": username, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")
    return encoded_jwt


