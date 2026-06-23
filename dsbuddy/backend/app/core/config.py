"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central config; all values overridable via env or .env file."""

    app_name: str = "Data Science Buddy API"
    app_version: str = "0.1.0"
    debug: bool = False

    anthropic_api_key: str = ""

    redis_url: str = "redis://redis:6379/0"

    max_file_size_mb: int = 100
    max_columns: int = 200
    sample_rows: int = 100_000

    llm_class: str = "claude-haiku-4-5-20251001"
    llm_reason: str = "claude-sonnet-4-6"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "protected_namespaces": ("settings_",),
    }


settings = Settings()
