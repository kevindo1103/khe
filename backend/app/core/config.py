import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Khế API"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours (#43/#46)

    # Bcrypt
    BCRYPT_ROUNDS: int = 12

    # DB
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    MASTER_DB_URL: str = f"sqlite:///{BASE_DIR / 'master.db'}"
    TENANTS_DIR: Path = BASE_DIR / "tenants"

    # Default tenant for dev
    DEFAULT_TENANT_ID: str = os.getenv("DEFAULT_TENANT_ID", "local-dev")

    # CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
