from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "NextStep"
    app_env: str = "development"
    database_url: str = "sqlite:///data/nextstep.db"
    cors_origins: str = ""
    admin_api_key: str = ""
    ai_provider: str = "noop"
    gemini_api_key: str = ""
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    ai_timeout_seconds: float = Field(default=15.0, gt=0, le=120)
    ai_max_tokens: int = Field(default=300, ge=32, le=2000)
    ai_temperature: float = Field(default=0.0, ge=0, le=2)
    ai_cache_ttl_seconds: int = Field(default=86400, ge=0, le=2_592_000)
    sync_on_start: bool = False
    data_source_urls: str = ""
    allowed_states: str = "PB,ALL"
    rate_limit_per_minute: int = Field(default=60, ge=1)
    request_body_limit_bytes: int = Field(default=32768, ge=1024)
    sync_timeout_seconds: float = Field(default=15.0, gt=0, le=120)
    audit_log_retention_days: int = Field(default=365, ge=1)
    auth_secret: str = "change-this-development-secret"
    auth_session_hours: int = Field(default=24, ge=1, le=720)

    @field_validator("ai_provider")
    @classmethod
    def normalize_provider(cls, value: str) -> str:
        return value.strip().lower() or "noop"

    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    def allowed_state_list(self) -> list[str]:
        values = [item.strip().upper() for item in self.allowed_states.split(",") if item.strip()]
        return values or ["PB", "ALL"]

    def data_source_url_list(self) -> list[str]:
        return [item.strip() for item in self.data_source_urls.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
