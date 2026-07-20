# IMPORTS
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Cash Managements"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str # generates with "openssl rand -hex 32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Security
    ALLOWED_ORIGINS: list[str] = [
        "https://cashmanagements.com",
        "https://localhost:3000", # Next.js dev
    ]

    model_config = ConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()