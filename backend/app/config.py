"""Application configuration using Pydantic Settings."""

from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite:///data/langear.db"

    # Google Gemini API
    gemini_api_key: str
    gemini_model_id: str = "gemini-3.1-flash-lite-preview"
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
    # "dashscope" uses real DashScope realtime ASR, "mock" keeps in-process fake stream.
    realtime_asr_provider: str = "dashscope"
    realtime_asr_model: str = "qwen3-asr-flash-realtime"
    realtime_asr_language: str = "zh"
    # Optional custom websocket endpoint for region-specific deployment.
    # Example: wss://dashscope.aliyuncs.com/api-ws/v1/realtime
    realtime_asr_ws_base_url: str | None = None

    # CORS
    cors_origins: str = "http://localhost:3002"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @model_validator(mode="after")
    def validate_ai_feedback_settings(self) -> "Settings":
        """Validate provider-specific AI feedback settings."""
        provider = self.ai_feedback_provider.strip().lower()
        if provider == "gemini" and not self.gemini_model_id.strip():
            raise ValueError(
                "GEMINI_MODEL_ID is required when AI_FEEDBACK_PROVIDER is 'gemini'"
            )
        return self


# Global settings instance
settings = Settings()
