from fastapi import Depends, Header, HTTPException, status
from common.core.security import verify_access_token
from common.core.settings import Settings, get_settings


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


def build_current_user_dep(settings: Settings | None = None):
    """Factory that returns a FastAPI dependency for the current user.

    Usage in each service:
        current_user_dep = build_current_user_dep(settings)
        @router.get("/endpoint")
        async def handler(user=Depends(current_user_dep)): ...
    """
    _settings = settings or get_settings()

    async def current_user_dep(authorization: str | None = Header(default=None)):
        return await get_current_user(authorization, _settings)

    return current_user_dep
