from datetime import datetime, timedelta

import jwt

secret_key = "drive_sync_secret_key"


def create_access_token(username: str):
    expire = datetime.utcnow()
    to_encode = {"sub": username, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")
    return encoded_jwt


def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            return False
        # Thêm bất kỳ kiểm tra bổ sung nào ở đây (nếu cần)
        return True
    except PyJWTError:
        return False
