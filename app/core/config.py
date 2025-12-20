"""
ABFI Intelligence Suite - Configuration
"""

from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_env: str = "development"
    secret_key: str = "change-me-in-production"
    api_key_header: str = "X-API-Key"

    # Database
    database_url: str = "postgresql+asyncpg://localhost:5432/abfi_ai"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # ML Model Paths
    model_cache_dir: str = "./models"
    sentiment_model_path: str = "./models/sentiment/deberta-v3-large-finetuned"
    policy_model_path: str = "./models/policy/classifier-v1"
    counterparty_model_path: str = "./models/counterparty/xgboost-v1"

    # MLflow
    mlflow_tracking_uri: str = "http://localhost:5000"
    mlflow_experiment_name: str = "abfi-intelligence"

    # ABFI Platform
    abfi_platform_api_url: str = "https://api.abfi.io"
    abfi_platform_api_key: str = ""

    # CORS
    cors_origins: List[str] = ["http://localhost:5173", "https://abfi.io"]

    # Monitoring
    prometheus_port: int = 9090
    enable_metrics: bool = True

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
