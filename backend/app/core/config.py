from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    project_name: str = Field(default="Financial Modeling Platform API", alias="PROJECT_NAME")
    version: str = Field(default="0.1.0", alias="VERSION")
    api_v1_prefix: str = "/api/v1"
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/financial_modeling",
        alias="DATABASE_URL",
    )
    sqlalchemy_echo: bool = Field(default=False, alias="SQLALCHEMY_ECHO")
    auto_create_tables: bool = Field(default=False, alias="AUTO_CREATE_TABLES")
    sec_user_agent: str = Field(
        default="Financial Modeling Platform contact@example.com",
        alias="SEC_USER_AGENT",
    )
    sec_request_timeout_seconds: int = Field(default=30, alias="SEC_REQUEST_TIMEOUT_SECONDS")
    reconciliation_tolerance_pct: float = Field(default=1.0, alias="RECONCILIATION_TOLERANCE_PCT")


@lru_cache
def get_settings() -> Settings:
    return Settings()
