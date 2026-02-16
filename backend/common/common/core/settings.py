from functools import lru_cache
from pathlib import Path
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


PROJECT_ROOT = Path(__file__).resolve().parents[4]
ROOT_ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    service_name: str = "service"
    env: str = "dev"
    debug: bool = True
    api_prefix: str = "/api/v1"
    cors_origins: str | list[AnyHttpUrl | str] = "http://localhost:3000"
    secret_key: str  # REQUIRED – no default; set SECRET_KEY env var
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 60 * 24
    supabase_db_url: str
    supabase_url: str = "https://example.supabase.co"
    supabase_anon_key: str = "dummy"
    supabase_service_role_key: str = "dummy"
    google_client_id: str = "dummy"
    redis_url: str = "redis://localhost:6379/0"
    llm_provider: str = "deepseek"
    huggingface_api_key: str = ""
    hf_llm_model: str = "mistralai/Mistral-7B-Instruct-v0.2"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    runpod_api_key: str = ""
    runpod_sdxl_endpoint: str = ""
    storage_bucket: str = "assets"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=str(ROOT_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


def mask_db_url(db_url: str) -> str:
    parsed = make_url(db_url)
    return str(parsed.set(password="***"))
