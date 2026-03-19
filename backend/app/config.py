"""Application configuration using Pydantic Settings."""

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite:///data/langear.db"

    # Google Gemini API
    gemini_api_key: str
    gemini_relay_base_url: str | None = None
    gemini_relay_api_key: str | None = None
    gemini_model_id: str | None = None
    gemini_prompt_version: str = "v1"

    # AI feedback provider
    ai_feedback_provider: str = "gemini"

    # Alibaba Cloud OSS
    oss_access_key_id: str
    oss_access_key_secret: str
    oss_endpoint: str
    oss_bucket_name: str
    oss_public_base_url: str
    # NOTE:
    # - STS client region id usually looks like: "cn-shanghai"
    # - OSS bucket region usually looks like: "oss-cn-shanghai"
    # We keep a single env var for simplicity and normalize where needed.
    oss_region: str | None = "cn-shanghai"

    # Alibaba Cloud STS (for temporary credentials)
    aliyun_role_arn: str  # RAM role ARN for AssumeRole

    # Alibaba Cloud ASR (DashScope)
    dashscope_api_key: str

    # CORS
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @model_validator(mode="after")
    def validate_ai_feedback_settings(self) -> "Settings":
        """Validate provider-specific AI feedback settings."""
        provider = self.ai_feedback_provider.strip().lower()
        if provider == "gemini" and not (self.gemini_model_id or "").strip():
            raise ValueError(
                "GEMINI_MODEL_ID is required when AI_FEEDBACK_PROVIDER is 'gemini'"
            )
        return self


# Global settings instance
settings = Settings()
