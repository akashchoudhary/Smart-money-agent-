from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://smartmoney:smartmoney123@localhost:5432/smartmoney_db"
    redis_url: str = "redis://localhost:6379"
    alert_webhook_url: str = ""
    alert_email: str = ""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    finnhub_api_key: str = ""
    alpha_vantage_api_key: str = ""
    master_score_alert_threshold: float = 85.0
    cache_ttl_seconds: int = 30

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
