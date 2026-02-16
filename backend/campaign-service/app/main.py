from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.core.settings import get_settings
from common.core.logging import configure_logging
from common.schemas.common import APIMessage
from app.api.v1.routes import router

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(title="Campaign Service", version="1.0.0", docs_url="/docs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(o) for o in settings.cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix=settings.api_prefix)


@app.get("/health", response_model=APIMessage)
async def health():
    return APIMessage(message="ok")

