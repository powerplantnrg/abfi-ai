"""
ABFI Intelligence Suite - Configuration
"""

from typing import List, Optional
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

    # Database - Turso (SQLite for serverless)
    turso_database_url: str = ""
    turso_auth_token: str = ""
    # Fallback to local SQLite for development
    database_url: str = "sqlite:///./abfi_intelligence.db"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis (optional for caching)
    redis_url: str = ""

    # OpenRouter for LLM-based analysis
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-3-haiku"  # Fast and cheap for analysis
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # ML Model Paths (fallback if no LLM)
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
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://abfi.io",
        "https://abfi-ai.vercel.app",
        "https://*.vercel.app",
    ]

    # Monitoring
    prometheus_port: int = 9090
    enable_metrics: bool = True

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Scraping settings
    scraping_enabled: bool = True
    scraping_rate_limit_seconds: float = 2.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
