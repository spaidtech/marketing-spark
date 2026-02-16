from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from common.core.settings import get_settings
from common.core.security import create_access_token, verify_google_id_token
from common.db.session import build_session_factory
from common.models import User
from common.schemas.common import TokenResponse

router = APIRouter(tags=["auth"])
settings = get_settings()
session_factory = build_session_factory(settings.supabase_db_url)


class GoogleLoginIn(BaseModel):
    credential: str


@router.post("/auth/google", response_model=TokenResponse)
async def google_login(payload: GoogleLoginIn) -> TokenResponse:
    try:
        info = verify_google_id_token(payload.credential, settings)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google credential"
        ) from exc

    async with session_factory() as db:
        existing = await db.execute(select(User).where(User.id == info["sub"]))
        user = existing.scalar_one_or_none()
        if not user:
            user = User(id=info["sub"], email=info["email"], name=info["name"])
            db.add(user)
            await db.commit()
        token = create_access_token(sub=user.id, email=user.email, settings=settings)
        return TokenResponse(
            access_token=token,
            expires_in=settings.jwt_exp_minutes * 60,
        )

