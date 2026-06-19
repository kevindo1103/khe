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

    # Source-tree root (where this code lives). Stable across envs.
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    # Runtime data root — master.db, tenants/, storage/ live here.
    # Defaults to BASE_DIR for local dev. In deployed envs set DATA_DIR to a path
    # OUTSIDE the rsync target (e.g. /opt/khe/data-staging) so code deploys
    # (`rsync --delete`) can never wipe SME data. See issue #87.
    DATA_DIR: Path = Path(os.getenv("DATA_DIR") or str(Path(__file__).resolve().parent.parent.parent))

    # Default tenant for dev
    DEFAULT_TENANT_ID: str = os.getenv("DEFAULT_TENANT_ID", "local-dev")

    # CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")

    # Telegram reminders (#62)
    TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: str | None = os.getenv("TELEGRAM_CHAT_ID")

    @property
    def MASTER_DB_URL(self) -> str:
        return f"sqlite:///{self.DATA_DIR / 'master.db'}"

    @property
    def TENANTS_DIR(self) -> Path:
        return self.DATA_DIR / "tenants"

    @property
    def STORAGE_DIR(self) -> Path:
        return self.DATA_DIR / "storage"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
