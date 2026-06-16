from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    pg_host: str = Field(default="127.0.0.1")
    pg_port: int = Field(default=6543)
    pg_db: str = Field(default="postgres")
    syntrix_app_password: str
    syntrix_admin_password: str

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://syntrix_app:{self.syntrix_app_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )

    @property
    def database_admin_url(self) -> str:
        return (
            f"postgresql+psycopg://syntrix_admin:{self.syntrix_admin_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
