import os
import bcrypt
import jwt
from datetime import datetime, timedelta

JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24 * 7  # token stays valid for 7 days


def hash_password(plain_password: str) -> str:
    password_bytes = plain_password.encode("utf-8")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        password_hash.encode("utf-8"),
    )


def create_access_token(user_id: str) -> str:
    """Builds a signed JWT that proves who the user is, without
    the server needing to remember anything (that's the point of JWTs:
    the token itself carries the proof)."""
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> str:
    """Verifies a token's signature and expiry, and returns the
    user_id it belongs to. Raises jwt exceptions if invalid/expired."""
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    return payload["sub"]