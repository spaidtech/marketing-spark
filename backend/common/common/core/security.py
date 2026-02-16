from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from google.oauth2 import id_token
from google.auth.transport import requests
from pydantic import BaseModel

from common.core.settings import Settings


class TokenPayload(BaseModel):
    sub: str
    email: str
    exp: int


def create_access_token(sub: str, email: str, settings: Settings) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_exp_minutes)
    payload = {"sub": sub, "email": email, "exp": int(expire.timestamp())}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def verify_access_token(token: str, settings: Settings) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return TokenPayload(**payload)
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc


def verify_google_id_token(credential: str, settings: Settings) -> dict:
    info = id_token.verify_oauth2_token(
        credential, requests.Request(), settings.google_client_id
    )
    return {"sub": info["sub"], "email": info["email"], "name": info.get("name", "")}

