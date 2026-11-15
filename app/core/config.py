from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    DATABASE_URL: str = "sqlite+aiosqlite:///./aiq_dev.db"
    TEST_DATABASE_URL: str | None = None
    SECRET_KEY: str = "dev-only-change-me"
    SQL_ECHO: bool = False
    ENVIRONMENT: str = "development"

settings = Settings()
