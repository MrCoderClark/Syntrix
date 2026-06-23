from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"


class GatewaySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ROOT_ENV),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    jwt_secret_key: str = Field(default="")
    redis_url: str = Field(default="redis://localhost:6379/0")
    gateway_port: int = Field(default=8002)
    heartbeat_interval: int = Field(default=30)
    heartbeat_timeout: int = Field(default=90)
    presence_ttl: int = Field(default=120)


@lru_cache
def get_settings() -> GatewaySettings:
    return GatewaySettings()
