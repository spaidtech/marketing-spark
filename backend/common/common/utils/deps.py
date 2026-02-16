from fastapi import Header, HTTPException, status
from common.core.security import verify_access_token
from common.core.settings import Settings


async def get_current_user(
    authorization: str | None,
    settings: Settings,
) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token"
        )
    token = authorization.split(" ", 1)[1]
    try:
        payload = verify_access_token(token, settings)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc
    return {"id": payload.sub, "email": payload.email}

