from fastapi import FastAPI, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from common.core.settings import get_settings, Settings
from common.core.logging import configure_logging, get_logger
from common.core.security import create_access_token
from common.db.session import build_session_factory
from common.models import User
from common.schemas.common import TokenResponse, UserProfile, APIMessage
from common.utils.deps import get_current_user
from app.api.v1.routes import router as auth_router

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger("auth-service")

app = FastAPI(
    title="Auth Service",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(o) for o in settings.cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router, prefix=settings.api_prefix)
session_factory: async_sessionmaker = build_session_factory(settings.supabase_db_url)


async def current_user_dep(authorization: str | None = Header(default=None)):
    return await get_current_user(authorization, settings)


@app.get("/health", response_model=APIMessage)
async def health() -> APIMessage:
    return APIMessage(message="ok")


@app.get("/api/v1/me", response_model=UserProfile)
async def me(user=Depends(current_user_dep)):
    async with session_factory() as db:
        result = await db.execute(select(User).where(User.id == user["id"]))
        db_user = result.scalar_one_or_none()
        if not db_user:
            return UserProfile(id=user["id"], email=user["email"], name="", credits_balance=0)
        return UserProfile(
            id=db_user.id,
            email=db_user.email,
            name=db_user.name,
            credits_balance=db_user.credits_balance,
        )


@app.post("/api/v1/dev-token", response_model=TokenResponse, include_in_schema=settings.env != "prod")
async def dev_token(email: str) -> TokenResponse:
    async with session_factory() as db:
        result = await db.execute(select(User).where(User.id == email))
        existing = result.scalar_one_or_none()
        if not existing:
            db.add(User(id=email, email=email, name="Dev User", credits_balance=100))
            await db.commit()
    token = create_access_token(sub=email, email=email, settings=settings)
    return TokenResponse(access_token=token, expires_in=settings.jwt_exp_minutes * 60)

