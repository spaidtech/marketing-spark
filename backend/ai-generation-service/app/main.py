from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import from_url
from sqlalchemy.engine import make_url

from common.core.settings import get_settings, mask_db_url
from common.core.logging import configure_logging, get_logger
from common.schemas.common import APIMessage
from common.utils.rate_limit import RateLimiter
from app.api.v1.routes import router, set_limiter

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger("ai-generation-service")

app = FastAPI(title="AI Generation Service", version="1.0.0", docs_url="/docs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(o) for o in settings.cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis_client = from_url(settings.redis_url, decode_responses=True)
set_limiter(RateLimiter(redis_client=redis_client, limit=40, window_seconds=60))
app.include_router(router, prefix=settings.api_prefix)


@app.on_event("startup")
async def startup_log_db_target() -> None:
    parsed = make_url(settings.supabase_db_url)
    logger.info(
        "db_config_loaded",
        db_url=mask_db_url(settings.supabase_db_url),
        db_user=parsed.username,
        db_host=parsed.host,
        db_port=parsed.port,
        db_name=parsed.database,
    )


@app.get("/health", response_model=APIMessage)
async def health():
    return APIMessage(message="ok")
