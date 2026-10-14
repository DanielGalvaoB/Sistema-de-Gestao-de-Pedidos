from datetime import timedelta

import bcrypt
import jwt

from app.config import settings
from app.core.utils import utcnow


def hash_password(password: str) -> str:
    # bcrypt considera apenas os primeiros 72 bytes
    pw = password.encode('utf-8')[:72]
    return bcrypt.hashpw(
        pw, bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    ).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode('utf-8')[:72], password_hash.encode('utf-8')
        )
    except ValueError:
        return False


def create_access_token(user_id: int) -> str:
    exp = utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {'sub': str(user_id), 'exp': exp}
    return jwt.encode(
        payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return int(payload['sub'])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
