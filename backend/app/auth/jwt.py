"""
JWT utilities: token creation and decoding.

SECRET_KEY should be set via the JWT_SECRET_KEY environment variable in production.
A fallback is provided for development only — never use it in production.
"""

import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, status

# In production, set JWT_SECRET_KEY as an environment variable.
SECRET_KEY = os.environ.get(
    "JWT_SECRET_KEY",
    "dev-secret-key-CHANGE-IN-PRODUCTION-32chars-min",  # fallback for dev ONLY
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "480"))  # 8 hours


def create_access_token(data: dict) -> str:
    """
    Create a signed JWT containing `data` plus an expiration claim.
    `data` should include at least {"sub": str(user_id)}.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT. Raises HTTP 401 on any failure.
    Returns the payload dict on success.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("sub") is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception
