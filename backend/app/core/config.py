import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/paint_db"
    SECRET_KEY: str = "gizli_anahtar_degistir"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    # Virgülle ayrılmış origin listesi; "*" = hepsi (sadece lokal geliştirme için)
    CORS_ORIGINS: str = "*"
    SQL_ECHO: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
