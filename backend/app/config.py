from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    APP_NAME: str = "HealthManage"
    ENV: str = "development"
    DATABASE_URL: str = "postgresql+psycopg2://healthmanage:healthmanage@localhost:5432/healthmanage"
    SECRET_KEY: str = "CHANGE_ME_dev_only_secret_do_not_use_in_prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
