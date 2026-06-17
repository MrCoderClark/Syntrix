from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ROOT_ENV),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    pg_host: str = Field(default="127.0.0.1")
    pg_port: int = Field(default=5432)
    pg_db: str = Field(default="postgres")
    pg_user: str = Field(default="postgres")
    pg_password: str = Field(default="postgres")

    # JWT
    jwt_secret_key: str = Field(default="")
    jwt_access_expire_minutes: int = Field(default=15)
    jwt_refresh_expire_days: int = Field(default=30)

    # OAuth — GitHub
    github_client_id: str = Field(default="")
    github_client_secret: str = Field(default="")

    # OAuth — Google
    google_client_id: str = Field(default="")
    google_client_secret: str = Field(default="")

    # OAuth — Discord
    discord_client_id: str = Field(default="")
    discord_client_secret: str = Field(default="")

    # Supabase Storage
    supabase_storage_url: str = Field(default="http://127.0.0.1:8000/storage/v1")
    supabase_service_key: str = Field(default="")
    storage_bucket: str = Field(default="syntrix-uploads")
    storage_max_size_bytes: int = Field(default=8_388_608)

    # Base URL for OAuth callbacks
    oauth_redirect_base_url: str = Field(default="http://127.0.0.1:8001")

    # Frontend URL for post-login redirect
    frontend_url: str = Field(default="http://127.0.0.1:3000")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.pg_user}:{self.pg_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )

    @property
    def database_admin_url(self) -> str:
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
