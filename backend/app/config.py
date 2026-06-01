"""应用配置"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://gamehub:gamehub@localhost:5432/gamehub"
    DATABASE_URL_SYNC: str = "postgresql://gamehub:gamehub@localhost:5432/gamehub"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "dev-secret-key-change-in-prod"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    STEAM_API_KEY: str = ""
    RAWG_API_KEY: str = ""

    # Social Media APIs
    YOUTUBE_API_KEY: str = ""
    TWITTER_BEARER_TOKEN: str = ""
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "GameHub/1.0"

    # Email
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@gamehub.local"

    class Config:
        env_file = ".env"


settings = Settings()
