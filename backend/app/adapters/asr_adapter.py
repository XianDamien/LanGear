"""Alibaba Cloud ASR adapter for speech transcription."""

from typing import Any

import dashscope
from dashscope.audio.asr import Recognition

from app.config import settings
from app.exceptions import ASRTranscriptionError


class ASRAdapter:
    """Adapter for Alibaba Cloud ASR (Automatic Speech Recognition).

    Uses DashScope qwen3-asr-flash model for speech-to-text transcription
    with word-level timestamps.
    """

    def __init__(self):
        """Initialize ASR client with API key from settings."""
        dashscope.api_key = settings.dashscope_api_key
        self.model = "qwen3-asr-flash"

    def transcribe(
        self,
        audio_url: str,
        timeout: int = 60,
    ) -> dict[str, Any]:
        """Transcribe audio to text using qwen3-asr-flash model.

        Args:
            audio_url: OSS signed URL of the audio file
            timeout: Request timeout in seconds (default: 60)

        Returns:
            Dictionary containing:
            - text: Complete transcription text
            - timestamps: List of word-level timestamps
                [{word: str, start: float, end: float}, ...]

        Raises:
            ASRTranscriptionError: If transcription fails
        """
        try:
            # Call qwen3-asr-flash API using file URL
            recognition = Recognition(
                model=self.model,
                format="wav",
                sample_rate=16000,
                callback=None,
            )

            # Use synchronous recognition with URL input
            result = recognition.call(
                file_urls=[audio_url],
                disfluency_removal_enabled=False,  # Keep disfluencies for accuracy
                timestamp_alignment_enabled=True,  # Enable word-level timestamps
                vocabulary_id=None,
            )

            # Check result status
            if result.status_code != 200:
                raise ASRTranscriptionError(
                    f"ASR API returned status {result.status_code}: {result.message}"
                )

            # Extract transcription and timestamps from response
            if not result.output or not result.output.get("results"):
                raise ASRTranscriptionError("No transcription in response")

            # Get the transcription result
            transcription_result = result.output["results"][0]
            full_text = transcription_result.get("transcription_text", "")

            # Extract word-level timestamps
            timestamps = []
            if "sentence" in transcription_result:
                for sentence in transcription_result["sentence"]:
                    if "words" in sentence:
                        for word_info in sentence["words"]:
                            timestamps.append(
                                {
                                    "word": word_info.get("text", ""),
                                    "start": word_info.get("begin_time", 0) / 1000.0,  # Convert ms to seconds
                                    "end": word_info.get("end_time", 0) / 1000.0,
                                }
                            )

            return {
                "text": full_text.strip(),
                "timestamps": timestamps,
            }

        except ASRTranscriptionError:
            raise
        except Exception as e:
            raise ASRTranscriptionError(f"ASR transcription failed: {str(e)}")
