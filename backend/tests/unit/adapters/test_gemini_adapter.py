"""Unit tests for Gemini adapter."""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from app.adapters.gemini_adapter import GeminiAdapter
from app.exceptions import AIFeedbackError


@pytest.mark.unit
class TestGeminiAdapter:
    """Test suite for GeminiAdapter."""

    @pytest.fixture
    def gemini_adapter(self, monkeypatch):
        """Create GeminiAdapter instance with mocked genai client."""
        import app.adapters.gemini_adapter as module

        mock_client = Mock()
        mock_genai_client = Mock(return_value=mock_client)
        monkeypatch.setattr(module.genai, "Client", mock_genai_client)

        object.__setattr__(module.settings, "gemini_api_key", "test-api-key")
        object.__setattr__(module.settings, "gemini_model_id", "gemini-test-model")

        adapter = GeminiAdapter()
        monkeypatch.setattr(adapter, "_download_audio_bytes", lambda *_args, **_kwargs: b"audio-bytes")
        return adapter, mock_client

    def test_uses_official_sdk_without_relay_options(self, monkeypatch):
        import app.adapters.gemini_adapter as module

        mock_client = Mock()
        mock_genai_client = Mock(return_value=mock_client)
        monkeypatch.setattr(module.genai, "Client", mock_genai_client)

        object.__setattr__(module.settings, "gemini_api_key", "test-api-key")
        object.__setattr__(module.settings, "gemini_model_id", "gemini-test-model")

        GeminiAdapter()

        mock_genai_client.assert_called_once_with(api_key="test-api-key")

    def test_load_prompt_from_task_directory(self, gemini_adapter):
        adapter, _ = gemini_adapter

        expected_dir = Path(adapter.prompts_dir)
        assert expected_dir.name == "prompts"
        assert (expected_dir / "single_feedback" / "system.md").exists()
        assert (expected_dir / "single_feedback" / "user.md").exists()
        assert (expected_dir / "single_feedback" / "metadata.json").exists()
        assert (expected_dir / "lesson_summary" / "system.md").exists()
        assert (expected_dir / "lesson_summary" / "user.md").exists()
        assert (expected_dir / "lesson_summary" / "metadata.json").exists()
        assert adapter.single_feedback_prompt.system
        assert adapter.single_feedback_prompt.user
        assert adapter.single_feedback_prompt.metadata["tracking_commit"] == "f0e005f"
        assert adapter.lesson_summary_prompt.system
        assert adapter.lesson_summary_prompt.user

    def test_generate_single_feedback_success(self, gemini_adapter):
        adapter, mock_client = gemini_adapter

        feedback_data = {
            "transcription_text": "Last week I went to the theatre",
            "pronunciation": "整体发音比较清楚。",
            "completeness": "关键信息基本完整。",
            "fluency": "整体较流畅，只有轻微停顿。",
            "suggestions": [
                {
                    "text": "把 theatre 的重音再拉开一点。",
                    "target_word": "theatre",
                    "timestamp": 1.2,
                }
            ],
            "issues": [
                {
                    "problem": "结尾辅音有一次没有收完整。",
                    "timestamp": 0.9,
                }
            ],
        }

        mock_response = Mock()
        mock_response.text = json.dumps(feedback_data)
        mock_client.models.generate_content.return_value = mock_response

        result = adapter.generate_single_feedback(
            front_text="Last week I went to the theatre.",
            user_audio_url="https://example.com/user.webm",
            reference_audio_url="https://example.com/ref.mp3",
        )

        assert result["pronunciation"] == "整体发音比较清楚。"
        assert result["issues"][0]["timestamp"] == 0.9
        assert result["suggestions"][0]["target_word"] == "theatre"
        assert result["transcription_text"] == "Last week I went to the theatre"

    def test_generate_single_feedback_markdown_json(self, gemini_adapter):
        adapter, mock_client = gemini_adapter

        feedback_data = {
            "transcription_text": "Test sentence",
            "pronunciation": "Good",
            "completeness": "Complete",
            "fluency": "Fluent",
            "suggestions": [],
            "issues": [],
        }

        mock_response = Mock()
        mock_response.text = f"```json\n{json.dumps(feedback_data)}\n```"
        mock_client.models.generate_content.return_value = mock_response

        result = adapter.generate_single_feedback(
            front_text="Test sentence",
            user_audio_url="https://example.com/user.wav",
            reference_audio_url="https://example.com/ref.wav",
        )

        assert result["pronunciation"] == "Good"
        assert result["issues"] == []

    def test_generate_single_feedback_requires_transcription_text(self, gemini_adapter):
        adapter, mock_client = gemini_adapter

        feedback_data = {
            "pronunciation": "好",
            "completeness": "完整",
            "fluency": "流畅",
            "suggestions": [],
            "issues": [],
        }

        mock_response = Mock()
        mock_response.text = json.dumps(feedback_data)
        mock_client.models.generate_content.return_value = mock_response

        with pytest.raises(AIFeedbackError) as exc_info:
            adapter.generate_single_feedback(
                front_text="Test sentence",
                user_audio_url="https://example.com/user.wav",
                reference_audio_url="https://example.com/ref.wav",
            )

        assert "Missing required field: transcription_text" in str(exc_info.value)

    def test_generate_single_feedback_missing_field(self, gemini_adapter):
        adapter, mock_client = gemini_adapter

        feedback_data = {
            "transcription_text": "test sentence",
            "pronunciation": "Good",
            "completeness": "Complete",
            "fluency": "Fluent",
            "suggestions": [],
            # missing issues
        }

        mock_response = Mock()
        mock_response.text = json.dumps(feedback_data)
        mock_client.models.generate_content.return_value = mock_response

        with pytest.raises(AIFeedbackError) as exc_info:
            adapter.generate_single_feedback(
                front_text="Test sentence",
                user_audio_url="https://example.com/user.wav",
                reference_audio_url="https://example.com/ref.wav",
            )

        assert "Missing required field: issues" in str(exc_info.value)

    def test_generate_single_feedback_invalid_issue_timestamp(self, gemini_adapter):
        adapter, mock_client = gemini_adapter

        feedback_data = {
            "transcription_text": "test sentence",
            "pronunciation": "Good",
            "completeness": "Complete",
            "fluency": "Fluent",
            "suggestions": [],
            "issues": [{"problem": "x", "timestamp": "bad"}],
        }

        mock_response = Mock()
        mock_response.text = json.dumps(feedback_data)
        mock_client.models.generate_content.return_value = mock_response

        with pytest.raises(AIFeedbackError) as exc_info:
            adapter.generate_single_feedback(
                front_text="Test sentence",
                user_audio_url="https://example.com/user.wav",
                reference_audio_url="https://example.com/ref.wav",
            )

        assert "issue.timestamp must be a number or null" in str(exc_info.value)

    def test_generate_single_feedback_supports_string_suggestions(self, gemini_adapter):
        adapter, mock_client = gemini_adapter

        feedback_data = {
            "transcription_text": "test sentence",
            "pronunciation": "Good",
            "completeness": "Complete",
            "fluency": "Fluent",
            "suggestions": ["Speak slightly slower"],
            "issues": [],
        }

        mock_response = Mock()
        mock_response.text = json.dumps(feedback_data)
        mock_client.models.generate_content.return_value = mock_response

        result = adapter.generate_single_feedback(
            front_text="Test sentence",
            user_audio_url="https://example.com/user.wav",
            reference_audio_url="https://example.com/ref.wav",
        )

        assert result["suggestions"][0]["text"] == "Speak slightly slower"
        assert result["suggestions"][0]["target_word"] is None

    def test_single_feedback_prompt_contract(self, gemini_adapter):
        adapter, _ = gemini_adapter
        system_prompt = adapter.single_feedback_prompt.system
        user_prompt = adapter.single_feedback_prompt.user

        assert "中文输出" in user_prompt
        assert "target_word" in user_prompt
        assert "原始英文词或英文短语" in user_prompt
        assert "问题发生的时间点" in system_prompt
        assert "问题发生的时间点" in user_prompt
        assert "字级时间戳" in system_prompt
        assert "词级时间戳" in user_prompt
        assert "transcription_timestamps" in user_prompt

    def test_generate_single_feedback_makes_single_audio_request_without_retry(self, gemini_adapter):
        adapter, mock_client = gemini_adapter

        mock_client.models.generate_content.side_effect = RuntimeError("bad request")

        with pytest.raises(AIFeedbackError) as exc_info:
            adapter.generate_single_feedback(
                front_text="Test sentence",
                user_audio_url="https://example.com/user.wav",
                reference_audio_url="https://example.com/ref.wav",
            )

        assert "Gemini audio request failed: bad request" in str(exc_info.value)
        assert mock_client.models.generate_content.call_count == 1

    def test_generate_lesson_summary_success(self, gemini_adapter):
        adapter, mock_client = gemini_adapter

        summary_data = {
            "overall": "Steady progress in this lesson.",
            "patterns": ["Minor ending-sound omissions"],
            "prioritized_actions": ["Practice final consonants"],
        }

        mock_response = Mock()
        mock_response.text = json.dumps(summary_data)
        mock_client.models.generate_content.return_value = mock_response

        result = adapter.generate_lesson_summary(feedbacks=[{"issues": []}])

        assert result["overall"].startswith("Steady")
        assert len(result["patterns"]) == 1

    def test_generate_lesson_summary_missing_field(self, gemini_adapter):
        adapter, mock_client = gemini_adapter

        summary_data = {
            "overall": "Good",
            "patterns": ["Pattern"],
            # missing prioritized_actions
        }

        mock_response = Mock()
        mock_response.text = json.dumps(summary_data)
        mock_client.models.generate_content.return_value = mock_response

        with pytest.raises(AIFeedbackError) as exc_info:
            adapter.generate_lesson_summary(feedbacks=[{"issues": []}])

        assert "Missing required field: prioritized_actions" in str(exc_info.value)

    def test_missing_prompt_directory_raises(self, gemini_adapter):
        adapter, _ = gemini_adapter
        with pytest.raises(AIFeedbackError) as exc_info:
            adapter._load_prompt("v999_not_exist")

        assert "Prompt directory not found" in str(exc_info.value)
