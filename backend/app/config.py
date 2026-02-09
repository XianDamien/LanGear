"""Application configuration using Pydantic Settings."""

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

    # Alibaba Cloud OSS
    oss_access_key_id: str
    oss_access_key_secret: str
    oss_endpoint: str
    oss_bucket_name: str
    oss_public_base_url: str
    oss_region: str | None = "cn-shanghai"  # OSS region for STS client

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


# Global settings instance
settings = Settings()
