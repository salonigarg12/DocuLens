from datetime import datetime, timedelta, timezone

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from pwdlib import PasswordHash

from app.config import (
    ACCESS_TOKEN_EXPIRE_DAYS,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
)


password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_hasher.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(username: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=ACCESS_TOKEN_EXPIRE_DAYS
    )

    payload = {
        "sub": username,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        username = payload.get("sub")

        if not username:
            raise ValueError(
                "Token does not contain a username."
            )

        return username

    except ExpiredSignatureError as exc:
        raise ValueError("Token has expired.") from exc

    except InvalidTokenError as exc:
        raise ValueError("Invalid token.") from exc