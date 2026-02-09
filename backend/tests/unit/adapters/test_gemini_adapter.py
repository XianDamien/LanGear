"""Unit tests for Gemini adapter.

Tests cover:
- Single-sentence feedback generation
- Lesson summary generation
- Timestamp association with suggestions
- JSON parsing and validation

All tests use mocks to avoid real Google Gemini API calls.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
from app.adapters.gemini_adapter import GeminiAdapter
from app.exceptions import AIFeedbackError


@pytest.mark.unit
class TestGeminiAdapter:
    """Test suite for GeminiAdapter."""

    @pytest.fixture
    def gemini_adapter(self):
        """Create GeminiAdapter instance with mocked genai."""
        with patch("app.adapters.gemini_adapter.genai") as mock_genai, \
             patch("app.adapters.gemini_adapter.Path.exists", return_value=False):

            adapter = GeminiAdapter()
            adapter.model = mock_genai.GenerativeModel.return_value

            yield adapter

    def test_generate_single_feedback_success(self, gemini_adapter):
        """Test successful single-sentence feedback generation."""
        # Arrange
        front_text = "Hello, how are you?"
        transcription = "Hello how are you"

        feedback_data = {
            "pronunciation": "Your pronunciation is clear and accurate.",
            "completeness": "You covered all words in the sentence.",
            "fluency": "Your speech flows naturally.",
            "suggestions": [
                {"text": "Add pauses between phrases", "target_word": None, "timestamp": None},
                {"text": "Emphasize 'are'", "target_word": "are", "timestamp": None}
            ]
        }

        mock_response = Mock()
        mock_response.text = json.dumps(feedback_data)
        gemini_adapter.model.generate_content = Mock(return_value=mock_response)

        # Act
        result = gemini_adapter.generate_single_feedback(front_text, transcription)

        # Assert
        assert result["pronunciation"] == "Your pronunciation is clear and accurate."
        assert result["completeness"] == "You covered all words in the sentence."
        assert result["fluency"] == "Your speech flows naturally."
        assert len(result["suggestions"]) == 2

    def test_generate_single_feedback_with_timestamps(self, gemini_adapter):
        """Test feedback generation with timestamp association."""
        # Arrange
        front_text = "The quick brown fox"
        transcription = "The quick brown fox"
        timestamps = [
            {"word": "The", "start": 0.0, "end": 0.2},
            {"word": "quick", "start": 0.2, "end": 0.5},
            {"word": "brown", "start": 0.5, "end": 0.8},
            {"word": "fox", "start": 0.8, "end": 1.1}
        ]

        feedback_data = {
            "pronunciation": "Good pronunciation overall.",
            "completeness": "Complete sentence.",
            "fluency": "Natural flow.",
            "suggestions": [
                {"text": "Improve 'quick' pronunciation", "target_word": "quick", "timestamp": None},
                {"text": "General suggestion", "target_word": None, "timestamp": None}
            ]
        }

        mock_response = Mock()
        mock_response.text = json.dumps(feedback_data)
        gemini_adapter.model.generate_content = Mock(return_value=mock_response)

        # Act
        result = gemini_adapter.generate_single_feedback(front_text, transcription, timestamps)

        # Assert
        assert len(result["suggestions"]) == 2
        # First suggestion should have timestamp associated
        assert result["suggestions"][0]["timestamp"] == 0.2
        # Second suggestion has no target_word, so no timestamp
        assert result["suggestions"][1]["timestamp"] is None

    def test_generate_single_feedback_json_with_markdown(self, gemini_adapter):
        """Test parsing JSON response wrapped in markdown code blocks."""
        # Arrange
        front_text = "Test sentence"
        transcription = "Test sentence"

        feedback_data = {
            "pronunciation": "Good",
            "completeness": "Complete",
            "fluency": "Fluent",
            "suggestions": []
        }

        mock_response = Mock()
        # Wrap JSON in markdown code block
        mock_response.text = f"```json\n{json.dumps(feedback_data)}\n```"
        gemini_adapter.model.generate_content = Mock(return_value=mock_response)

        # Act
        result = gemini_adapter.generate_single_feedback(front_text, transcription)

        # Assert
        assert result["pronunciation"] == "Good"
        assert result["completeness"] == "Complete"
        assert result["fluency"] == "Fluent"

    def test_generate_single_feedback_json_plain_markdown(self, gemini_adapter):
        """Test parsing JSON response with plain markdown code blocks."""
        # Arrange
        front_text = "Test"
        transcription = "Test"

        feedback_data = {
            "pronunciation": "Excellent",
            "completeness": "Full",
            "fluency": "Smooth",
            "suggestions": []
        }

        mock_response = Mock()
        # Wrap JSON in plain markdown code block (no language specifier)
        mock_response.text = f"```\n{json.dumps(feedback_data)}\n```"
        gemini_adapter.model.generate_content = Mock(return_value=mock_response)

        # Act
        result = gemini_adapter.generate_single_feedback(front_text, transcription)

        # Assert
        assert result["pronunciation"] == "Excellent"

    def test_generate_single_feedback_missing_field(self, gemini_adapter):
        """Test error handling when required field is missing."""
        # Arrange
        front_text = "Test"
        transcription = "Test"

        # Missing 'fluency' field
        feedback_data = {
            "pronunciation": "Good",
            "completeness": "Complete",
            "suggestions": []
        }

        mock_response = Mock()
        mock_response.text = json.dumps(feedback_data)
        gemini_adapter.model.generate_content = Mock(return_value=mock_response)

        # Act & Assert
        with pytest.raises(AIFeedbackError) as exc_info:
            gemini_adapter.generate_single_feedback(front_text, transcription)

        assert "Missing required field: fluency" in str(exc_info.value)

    def test_generate_single_feedback_invalid_json(self, gemini_adapter):
        """Test error handling for invalid JSON response."""
        # Arrange
        front_text = "Test"
        transcription = "Test"

        mock_response = Mock()
        mock_response.text = "This is not valid JSON {{}}"
        gemini_adapter.model.generate_content = Mock(return_value=mock_response)

        # Act & Assert
        with pytest.raises(AIFeedbackError) as exc_info:
            gemini_adapter.generate_single_feedback(front_text, transcription)

        assert "Failed to parse JSON response" in str(exc_info.value)

    def test_generate_single_feedback_api_exception(self, gemini_adapter):
        """Test error handling when API raises exception."""
        # Arrange
        front_text = "Test"
        transcription = "Test"

        gemini_adapter.model.generate_content = Mock(
            side_effect=Exception("API rate limit exceeded")
        )

        # Act & Assert
        with pytest.raises(AIFeedbackError) as exc_info:
            gemini_adapter.generate_single_feedback(front_text, transcription)

        assert "API rate limit exceeded" in str(exc_info.value)

    def test_generate_single_feedback_with_custom_prompt(self, gemini_adapter):
        """Test feedback generation with custom prompt template."""
        # Arrange
        custom_prompt = "Evaluate: {original_text} vs {user_transcription}"
        gemini_adapter.single_feedback_prompt = custom_prompt

        front_text = "Hello world"
        transcription = "Hello world"

        feedback_data = {
            "pronunciation": "Good",
            "completeness": "Complete",
            "fluency": "Fluent",
            "suggestions": []
        }

        mock_response = Mock()
        mock_response.text = json.dumps(feedback_data)
        gemini_adapter.model.generate_content = Mock(return_value=mock_response)

        # Act
        result = gemini_adapter.generate_single_feedback(front_text, transcription)

        # Assert
        assert result["pronunciation"] == "Good"
        # Verify the prompt was formatted correctly
        call_args = gemini_adapter.model.generate_content.call_args[0]
        assert "Hello world" in call_args[0]

    def test_generate_lesson_summary_success(self, gemini_adapter):
        """Test successful lesson summary generation."""
        # Arrange
        feedbacks = [
            {
                "pronunciation": "Good pronunciation",
                "completeness": "Complete",
                "fluency": "Natural",
                "suggestions": ["Work on 'th' sounds"]
            },
            {
                "pronunciation": "Clear speech",
                "completeness": "Full coverage",
                "fluency": "Smooth",
                "suggestions": ["Improve pacing"]
            }
        ]

        summary_data = {
            "overall": "Excellent performance on this lesson",
            "patterns": ["Consistent pronunciation issues with 'th'", "Good fluency overall"],
            "prioritized_actions": ["Practice 'th' sounds", "Work on pacing", "Keep up the good work"]
        }

        mock_response = Mock()
        mock_response.text = json.dumps(summary_data)
        gemini_adapter.model.generate_content = Mock(return_value=mock_response)

        # Act
        result = gemini_adapter.generate_lesson_summary(feedbacks)

        # Assert
        assert result["overall"] == "Excellent performance on this lesson"
        assert len(result["patterns"]) == 2
        assert len(result["prioritized_actions"]) == 3

    def test_generate_lesson_summary_with_markdown(self, gemini_adapter):
        """Test lesson summary parsing with markdown code blocks."""
        # Arrange
        feedbacks = [{"pronunciation": "Good", "completeness": "Complete", "fluency": "Smooth", "suggestions": []}]

        summary_data = {
            "overall": "Great job",
            "patterns": ["Pattern 1"],
            "prioritized_actions": ["Action 1"]
        }

        mock_response = Mock()
        mock_response.text = f"```json\n{json.dumps(summary_data)}\n```"
        gemini_adapter.model.generate_content = Mock(return_value=mock_response)

        # Act
        result = gemini_adapter.generate_lesson_summary(feedbacks)

        # Assert
        assert result["overall"] == "Great job"

    def test_generate_lesson_summary_missing_field(self, gemini_adapter):
        """Test error handling when summary is missing required field."""
        # Arrange
        feedbacks = [{"pronunciation": "Good", "completeness": "Complete", "fluency": "Smooth", "suggestions": []}]

        # Missing 'prioritized_actions' field
        summary_data = {
            "overall": "Good",
            "patterns": ["Pattern 1"]
        }

        mock_response = Mock()
        mock_response.text = json.dumps(summary_data)
        gemini_adapter.model.generate_content = Mock(return_value=mock_response)

        # Act & Assert
        with pytest.raises(AIFeedbackError) as exc_info:
            gemini_adapter.generate_lesson_summary(feedbacks)

        assert "Missing required field: prioritized_actions" in str(exc_info.value)

    def test_generate_lesson_summary_invalid_json(self, gemini_adapter):
        """Test error handling for invalid JSON in summary."""
        # Arrange
        feedbacks = [{"pronunciation": "Good", "completeness": "Complete", "fluency": "Smooth", "suggestions": []}]

        mock_response = Mock()
        mock_response.text = "Invalid JSON content"
        gemini_adapter.model.generate_content = Mock(return_value=mock_response)

        # Act & Assert
        with pytest.raises(AIFeedbackError) as exc_info:
            gemini_adapter.generate_lesson_summary(feedbacks)

        assert "Failed to parse JSON response" in str(exc_info.value)

    def test_generate_lesson_summary_with_custom_prompt(self, gemini_adapter):
        """Test summary generation with custom prompt template."""
        # Arrange
        custom_prompt = "Summarize these feedbacks: {feedbacks_json}"
        gemini_adapter.lesson_summary_prompt = custom_prompt

        feedbacks = [{"pronunciation": "Good", "completeness": "Complete", "fluency": "Smooth", "suggestions": []}]

        summary_data = {
            "overall": "Good overall",
            "patterns": ["Pattern"],
            "prioritized_actions": ["Action"]
        }

        mock_response = Mock()
        mock_response.text = json.dumps(summary_data)
        gemini_adapter.model.generate_content = Mock(return_value=mock_response)

        # Act
        result = gemini_adapter.generate_lesson_summary(feedbacks)

        # Assert
        assert result["overall"] == "Good overall"

    def test_associate_timestamps_case_insensitive(self, gemini_adapter):
        """Test that timestamp association is case-insensitive."""
        # Arrange
        feedback = {
            "suggestions": [
                {"text": "Fix this", "target_word": "HELLO", "timestamp": None},
                {"text": "Fix that", "target_word": "World", "timestamp": None}
            ]
        }

        timestamps = [
            {"word": "hello", "start": 0.0, "end": 0.5},
            {"word": "WORLD", "start": 0.5, "end": 1.0}
        ]

        # Act
        result = gemini_adapter._associate_timestamps(feedback, timestamps)

        # Assert
        assert result["suggestions"][0]["timestamp"] == 0.0
        assert result["suggestions"][1]["timestamp"] == 0.5

    def test_associate_timestamps_no_match(self, gemini_adapter):
        """Test timestamp association when target word not found."""
        # Arrange
        feedback = {
            "suggestions": [
                {"text": "Fix pronunciation", "target_word": "nonexistent", "timestamp": None}
            ]
        }

        timestamps = [
            {"word": "hello", "start": 0.0, "end": 0.5}
        ]

        # Act
        result = gemini_adapter._associate_timestamps(feedback, timestamps)

        # Assert
        # timestamp should remain None when word not found
        assert result["suggestions"][0]["timestamp"] is None

    def test_associate_timestamps_no_target_word(self, gemini_adapter):
        """Test timestamp association when suggestion has no target_word."""
        # Arrange
        feedback = {
            "suggestions": [
                {"text": "General suggestion", "target_word": None, "timestamp": None}
            ]
        }

        timestamps = [
            {"word": "hello", "start": 0.0, "end": 0.5}
        ]

        # Act
        result = gemini_adapter._associate_timestamps(feedback, timestamps)

        # Assert
        assert result["suggestions"][0]["timestamp"] is None

    def test_associate_timestamps_empty_timestamps(self, gemini_adapter):
        """Test timestamp association with empty timestamp list."""
        # Arrange
        feedback = {
            "suggestions": [
                {"text": "Fix this", "target_word": "hello", "timestamp": None}
            ]
        }

        timestamps = []

        # Act
        result = gemini_adapter._associate_timestamps(feedback, timestamps)

        # Assert
        assert result["suggestions"][0]["timestamp"] is None

    def test_load_prompt_file_exists(self):
        """Test loading prompt from existing file."""
        # Arrange
        prompt_content = "Test prompt template: {original_text}"

        with patch("app.adapters.gemini_adapter.genai"), \
             patch("app.adapters.gemini_adapter.Path.exists", return_value=True), \
             patch("app.adapters.gemini_adapter.Path.read_text", return_value=prompt_content):

            # Act
            adapter = GeminiAdapter()

        # Assert
        assert adapter.single_feedback_prompt == prompt_content

    def test_load_prompt_file_not_exists(self):
        """Test loading prompt when file doesn't exist."""
        # Arrange
        with patch("app.adapters.gemini_adapter.genai"), \
             patch("app.adapters.gemini_adapter.Path.exists", return_value=False):

            # Act
            adapter = GeminiAdapter()

        # Assert
        assert adapter.single_feedback_prompt == ""
        assert adapter.lesson_summary_prompt == ""
