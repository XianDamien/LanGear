"""Unit tests for ASR adapter.

Tests cover:
- Audio transcription with word-level timestamps
- Response format validation
- Error handling

All tests use mocks to avoid real Dashscope API calls.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.adapters.asr_adapter import ASRAdapter
from app.exceptions import ASRTranscriptionError


@pytest.mark.unit
class TestASRAdapter:
    """Test suite for ASRAdapter."""

    @pytest.fixture
    def asr_adapter(self):
        """Create ASRAdapter instance with mocked dashscope."""
        with patch("app.adapters.asr_adapter.dashscope") as mock_dashscope:
            adapter = ASRAdapter()
            yield adapter

    def test_transcribe_success(self, asr_adapter):
        """Test successful audio transcription with timestamps."""
        # Arrange
        audio_url = "https://oss.example.com/test.wav"

        # Mock successful ASR response
        mock_result = Mock()
        mock_result.status_code = 200
        mock_result.output = {
            "results": [
                {
                    "transcription_text": "Hello world this is a test",
                    "sentence": [
                        {
                            "words": [
                                {"text": "Hello", "begin_time": 0, "end_time": 500},
                                {"text": "world", "begin_time": 500, "end_time": 1000},
                                {"text": "this", "begin_time": 1000, "end_time": 1300},
                                {"text": "is", "begin_time": 1300, "end_time": 1500},
                                {"text": "a", "begin_time": 1500, "end_time": 1600},
                                {"text": "test", "begin_time": 1600, "end_time": 2000},
                            ]
                        }
                    ]
                }
            ]
        }

        with patch("app.adapters.asr_adapter.Recognition") as mock_recognition_class:
            mock_recognition = MagicMock()
            mock_recognition.call.return_value = mock_result
            mock_recognition_class.return_value = mock_recognition

            # Act
            result = asr_adapter.transcribe(audio_url)

        # Assert
        assert result["text"] == "Hello world this is a test"
        assert len(result["timestamps"]) == 6

        # Verify timestamp format and conversion from ms to seconds
        assert result["timestamps"][0] == {"word": "Hello", "start": 0.0, "end": 0.5}
        assert result["timestamps"][1] == {"word": "world", "start": 0.5, "end": 1.0}
        assert result["timestamps"][5] == {"word": "test", "start": 1.6, "end": 2.0}

    def test_transcribe_multiple_sentences(self, asr_adapter):
        """Test transcription with multiple sentences."""
        # Arrange
        audio_url = "https://oss.example.com/test.wav"

        mock_result = Mock()
        mock_result.status_code = 200
        mock_result.output = {
            "results": [
                {
                    "transcription_text": "First sentence. Second sentence.",
                    "sentence": [
                        {
                            "words": [
                                {"text": "First", "begin_time": 0, "end_time": 400},
                                {"text": "sentence", "begin_time": 400, "end_time": 900},
                            ]
                        },
                        {
                            "words": [
                                {"text": "Second", "begin_time": 1000, "end_time": 1400},
                                {"text": "sentence", "begin_time": 1400, "end_time": 1900},
                            ]
                        }
                    ]
                }
            ]
        }

        with patch("app.adapters.asr_adapter.Recognition") as mock_recognition_class:
            mock_recognition = MagicMock()
            mock_recognition.call.return_value = mock_result
            mock_recognition_class.return_value = mock_recognition

            # Act
            result = asr_adapter.transcribe(audio_url)

        # Assert
        assert result["text"] == "First sentence. Second sentence."
        assert len(result["timestamps"]) == 4
        assert result["timestamps"][2]["word"] == "Second"

    def test_transcribe_custom_timeout(self, asr_adapter):
        """Test transcription with custom timeout."""
        # Arrange
        audio_url = "https://oss.example.com/test.wav"
        timeout = 120

        mock_result = Mock()
        mock_result.status_code = 200
        mock_result.output = {
            "results": [
                {
                    "transcription_text": "Test",
                    "sentence": [
                        {
                            "words": [
                                {"text": "Test", "begin_time": 0, "end_time": 500},
                            ]
                        }
                    ]
                }
            ]
        }

        with patch("app.adapters.asr_adapter.Recognition") as mock_recognition_class:
            mock_recognition = MagicMock()
            mock_recognition.call.return_value = mock_result
            mock_recognition_class.return_value = mock_recognition

            # Act
            result = asr_adapter.transcribe(audio_url, timeout=timeout)

        # Assert
        assert result["text"] == "Test"
        # Verify Recognition was initialized correctly
        mock_recognition_class.assert_called_once()

    def test_transcribe_api_error_status(self, asr_adapter):
        """Test transcription with API error status."""
        # Arrange
        audio_url = "https://oss.example.com/test.wav"

        mock_result = Mock()
        mock_result.status_code = 500
        mock_result.message = "Internal server error"

        with patch("app.adapters.asr_adapter.Recognition") as mock_recognition_class:
            mock_recognition = MagicMock()
            mock_recognition.call.return_value = mock_result
            mock_recognition_class.return_value = mock_recognition

            # Act & Assert
            with pytest.raises(ASRTranscriptionError) as exc_info:
                asr_adapter.transcribe(audio_url)

            assert "ASR API returned status 500" in str(exc_info.value)

    def test_transcribe_empty_response(self, asr_adapter):
        """Test transcription with empty response."""
        # Arrange
        audio_url = "https://oss.example.com/test.wav"

        mock_result = Mock()
        mock_result.status_code = 200
        mock_result.output = None

        with patch("app.adapters.asr_adapter.Recognition") as mock_recognition_class:
            mock_recognition = MagicMock()
            mock_recognition.call.return_value = mock_result
            mock_recognition_class.return_value = mock_recognition

            # Act & Assert
            with pytest.raises(ASRTranscriptionError) as exc_info:
                asr_adapter.transcribe(audio_url)

            assert "No transcription in response" in str(exc_info.value)

    def test_transcribe_missing_results(self, asr_adapter):
        """Test transcription with missing results field."""
        # Arrange
        audio_url = "https://oss.example.com/test.wav"

        mock_result = Mock()
        mock_result.status_code = 200
        mock_result.output = {"results": []}

        with patch("app.adapters.asr_adapter.Recognition") as mock_recognition_class:
            mock_recognition = MagicMock()
            mock_recognition.call.return_value = mock_result
            mock_recognition_class.return_value = mock_recognition

            # Act & Assert
            with pytest.raises(ASRTranscriptionError) as exc_info:
                asr_adapter.transcribe(audio_url)

            assert "No transcription in response" in str(exc_info.value)

    def test_transcribe_exception(self, asr_adapter):
        """Test transcription with general exception."""
        # Arrange
        audio_url = "https://oss.example.com/test.wav"

        with patch("app.adapters.asr_adapter.Recognition") as mock_recognition_class:
            mock_recognition_class.side_effect = Exception("Network timeout")

            # Act & Assert
            with pytest.raises(ASRTranscriptionError) as exc_info:
                asr_adapter.transcribe(audio_url)

            assert "ASR transcription failed" in str(exc_info.value)

    def test_transcribe_no_timestamps(self, asr_adapter):
        """Test transcription when word-level timestamps are not available."""
        # Arrange
        audio_url = "https://oss.example.com/test.wav"

        mock_result = Mock()
        mock_result.status_code = 200
        mock_result.output = {
            "results": [
                {
                    "transcription_text": "Text without timestamps",
                    # No 'sentence' field
                }
            ]
        }

        with patch("app.adapters.asr_adapter.Recognition") as mock_recognition_class:
            mock_recognition = MagicMock()
            mock_recognition.call.return_value = mock_result
            mock_recognition_class.return_value = mock_recognition

            # Act
            result = asr_adapter.transcribe(audio_url)

        # Assert
        assert result["text"] == "Text without timestamps"
        assert result["timestamps"] == []

    def test_transcribe_partial_timestamps(self, asr_adapter):
        """Test transcription with partial timestamp data."""
        # Arrange
        audio_url = "https://oss.example.com/test.wav"

        mock_result = Mock()
        mock_result.status_code = 200
        mock_result.output = {
            "results": [
                {
                    "transcription_text": "Partial data",
                    "sentence": [
                        {
                            "words": [
                                # Missing some fields
                                {"text": "Partial"},
                                {"text": "data", "begin_time": 500},
                            ]
                        }
                    ]
                }
            ]
        }

        with patch("app.adapters.asr_adapter.Recognition") as mock_recognition_class:
            mock_recognition = MagicMock()
            mock_recognition.call.return_value = mock_result
            mock_recognition_class.return_value = mock_recognition

            # Act
            result = asr_adapter.transcribe(audio_url)

        # Assert
        assert result["text"] == "Partial data"
        assert len(result["timestamps"]) == 2
        # Missing fields should default to empty string or 0
        assert result["timestamps"][0]["word"] == "Partial"
        assert result["timestamps"][0]["start"] == 0.0
        assert result["timestamps"][0]["end"] == 0.0

    def test_transcribe_strips_whitespace(self, asr_adapter):
        """Test that transcription text is properly stripped."""
        # Arrange
        audio_url = "https://oss.example.com/test.wav"

        mock_result = Mock()
        mock_result.status_code = 200
        mock_result.output = {
            "results": [
                {
                    "transcription_text": "  Text with whitespace  \n",
                    "sentence": []
                }
            ]
        }

        with patch("app.adapters.asr_adapter.Recognition") as mock_recognition_class:
            mock_recognition = MagicMock()
            mock_recognition.call.return_value = mock_result
            mock_recognition_class.return_value = mock_recognition

            # Act
            result = asr_adapter.transcribe(audio_url)

        # Assert
        assert result["text"] == "Text with whitespace"

    def test_transcribe_recognition_parameters(self, asr_adapter):
        """Test that Recognition is called with correct parameters."""
        # Arrange
        audio_url = "https://oss.example.com/test.wav"

        mock_result = Mock()
        mock_result.status_code = 200
        mock_result.output = {
            "results": [
                {
                    "transcription_text": "Test",
                    "sentence": []
                }
            ]
        }

        with patch("app.adapters.asr_adapter.Recognition") as mock_recognition_class:
            mock_recognition = MagicMock()
            mock_recognition.call.return_value = mock_result
            mock_recognition_class.return_value = mock_recognition

            # Act
            asr_adapter.transcribe(audio_url)

        # Assert - verify Recognition initialization
        mock_recognition_class.assert_called_once_with(
            model="qwen3-asr-flash",
            format="wav",
            sample_rate=16000,
            callback=None,
        )

        # Verify call parameters
        mock_recognition.call.assert_called_once()
        call_kwargs = mock_recognition.call.call_args[1]
        assert call_kwargs["file_urls"] == [audio_url]
        assert call_kwargs["disfluency_removal_enabled"] is False
        assert call_kwargs["timestamp_alignment_enabled"] is True
        assert call_kwargs["vocabulary_id"] is None
