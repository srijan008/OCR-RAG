"""
JWT Authentication service.
Handles password hashing (bcrypt) and JWT token creation/verification.
"""
from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
from app.config import get_settings

settings = get_settings()

# removed pwd_context for direct bcrypt usage

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def hash_password(password: str) -> str:
    # Bcrypt has a 72-byte limit. Truncate manually to avoid library-level ValueError
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    pwd_bytes = plain.encode("utf-8")[:72]
    hashed_bytes = hashed.encode("utf-8")
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)


def create_access_token(user_id: int, email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "email": email, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode a JWT and return its payload. Raises JWTError on failure."""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
