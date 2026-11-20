from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "sqlite+aiosqlite:///./aiq_dev.db"
    TEST_DATABASE_URL: str | None = None
    SECRET_KEY: str = "dev-only-change-me"
    SQL_ECHO: bool = False
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://127.0.0.1:8000,http://localhost:8000"

    @model_validator(mode="after")
    def validate_security_settings(self):
        environment = self.ENVIRONMENT.strip().lower()
        if environment not in {"development", "dev", "test"}:
            if self.SECRET_KEY == "dev-only-change-me" or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "SECRET_KEY must be set to a random value of at least 32 characters "
                    "outside development/test environments"
                )
        return self

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()
