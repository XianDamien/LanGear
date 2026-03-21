"""Unit tests for configuration validation."""

import pytest
from pydantic import ValidationError

from app.config import Settings


@pytest.mark.unit
def test_gemini_model_id_cannot_be_blank_for_gemini_provider():
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            _env_file=None,
            database_url="sqlite:///data/langear.db",
            gemini_api_key="test-key",
            gemini_model_id="   ",
            ai_feedback_provider="gemini",
            oss_access_key_id="id",
            oss_access_key_secret="secret",
            oss_endpoint="oss-cn-shanghai.aliyuncs.com",
            oss_bucket_name="bucket",
            oss_public_base_url="https://bucket.oss-cn-shanghai.aliyuncs.com",
            aliyun_role_arn="acs:ram::123456789012:role/test",
            dashscope_api_key="dashscope-key",
        )

    assert "GEMINI_MODEL_ID is required" in str(exc_info.value)


@pytest.mark.unit
def test_gemini_settings_use_default_model_id():
    settings = Settings(
        _env_file=None,
        database_url="sqlite:///data/langear.db",
        gemini_api_key="test-key",
        ai_feedback_provider="gemini",
        oss_access_key_id="id",
        oss_access_key_secret="secret",
        oss_endpoint="oss-cn-shanghai.aliyuncs.com",
        oss_bucket_name="bucket",
        oss_public_base_url="https://bucket.oss-cn-shanghai.aliyuncs.com",
        aliyun_role_arn="acs:ram::123456789012:role/test",
        dashscope_api_key="dashscope-key",
    )

    assert settings.gemini_model_id == "gemini-3.1-flash-lite-preview"


@pytest.mark.unit
def test_gemini_settings_pass_with_explicit_model_id():
    settings = Settings(
        _env_file=None,
        database_url="sqlite:///data/langear.db",
        gemini_api_key="test-key",
        gemini_model_id="gemini-3.1-flash-lite-preview",
        ai_feedback_provider="gemini",
        oss_access_key_id="id",
        oss_access_key_secret="secret",
        oss_endpoint="oss-cn-shanghai.aliyuncs.com",
        oss_bucket_name="bucket",
        oss_public_base_url="https://bucket.oss-cn-shanghai.aliyuncs.com",
        aliyun_role_arn="acs:ram::123456789012:role/test",
        dashscope_api_key="dashscope-key",
    )

    assert settings.gemini_model_id == "gemini-3.1-flash-lite-preview"


@pytest.mark.unit
def test_non_gemini_provider_can_skip_gemini_model_id():
    settings = Settings(
        _env_file=None,
        database_url="sqlite:///data/langear.db",
        gemini_api_key="test-key",
        ai_feedback_provider="mock-provider",
        oss_access_key_id="id",
        oss_access_key_secret="secret",
        oss_endpoint="oss-cn-shanghai.aliyuncs.com",
        oss_bucket_name="bucket",
        oss_public_base_url="https://bucket.oss-cn-shanghai.aliyuncs.com",
        aliyun_role_arn="acs:ram::123456789012:role/test",
        dashscope_api_key="dashscope-key",
    )

    assert settings.ai_feedback_provider == "mock-provider"
    assert settings.gemini_model_id == "gemini-3.1-flash-lite-preview"
