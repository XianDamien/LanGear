"""Google Gemini adapter for AI evaluation."""

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen

from google import genai
from google.genai import types

from app.config import settings
from app.exceptions import AIFeedbackError


class GeminiAdapter:
    """Adapter for Google Gemini AI multimodal evaluation."""

    def __init__(self):
        """Initialize Gemini client, model, and prompt templates."""
        api_key = settings.gemini_relay_api_key or settings.gemini_api_key
        if not api_key:
            raise AIFeedbackError("Missing Gemini API key")

        http_options: types.HttpOptions | None = None
        if settings.gemini_relay_base_url:
            headers: dict[str, str] | None = None
            if settings.gemini_relay_api_key:
                headers = {"Authorization": f"Bearer {settings.gemini_relay_api_key}"}
            http_options = types.HttpOptions(
                base_url=settings.gemini_relay_base_url,
                headers=headers,
            )

        self.client = genai.Client(api_key=api_key, http_options=http_options)
        self.model_id = settings.gemini_model_id or ""
        self.prompts_dir = Path(__file__).parent / "prompts" / settings.gemini_prompt_version

        self.single_feedback_prompt = self._load_prompt("single_feedback.txt")
        self.lesson_summary_prompt = self._load_prompt("lesson_summary.txt")

    def _load_prompt(self, filename: str) -> str:
        """Load prompt template from versioned prompt directory."""
        prompt_file = self.prompts_dir / filename
        if not prompt_file.exists():
            raise AIFeedbackError(f"Prompt file not found: {prompt_file}")

        content = prompt_file.read_text(encoding="utf-8").strip()
        if not content:
            raise AIFeedbackError(f"Prompt file is empty: {prompt_file}")
        return content

    @staticmethod
    def _render_prompt(template: str, **variables: Any) -> str:
        """Render placeholders without interpreting JSON braces in templates."""
        rendered = template
        for key, value in variables.items():
            rendered = rendered.replace(f"{{{key}}}", str(value))
        return rendered

    @staticmethod
    def _extract_json_text(raw_text: str) -> str:
        """Extract JSON payload from model output text."""
        result_text = raw_text.strip()

        if result_text.startswith("```"):
            parts = result_text.split("```")
            if len(parts) >= 2:
                result_text = parts[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()

        return result_text

    @staticmethod
    def _guess_audio_mime_type(audio_url: str) -> str:
        """Best-effort MIME type inference by URL suffix."""
        path = urlparse(audio_url).path.lower()
        if path.endswith(".wav"):
            return "audio/wav"
        if path.endswith(".webm"):
            return "audio/webm"
        if path.endswith(".mp3"):
            return "audio/mpeg"
        if path.endswith(".m4a"):
            return "audio/mp4"
        if path.endswith(".ogg"):
            return "audio/ogg"
        return "application/octet-stream"

    @staticmethod
    def _download_audio_bytes(audio_url: str, timeout: int = 30) -> bytes:
        """Download audio bytes for inline fallback."""
        try:
            with urlopen(audio_url, timeout=timeout) as response:
                data = response.read()
                if not data:
                    raise AIFeedbackError(f"Empty audio content: {audio_url}")
                return data
        except AIFeedbackError:
            raise
        except Exception as e:
            raise AIFeedbackError(f"Failed to download audio: {audio_url}, error={e}")

    def _generate_with_audio(
        self,
        prompt: str,
        user_audio_url: str,
        reference_audio_url: str,
        max_output_tokens: int,
    ) -> str:
        """Generate multimodal response with URL-first and inline-audio fallback."""
        config = types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=max_output_tokens,
            response_mime_type="application/json",
        )

        user_mime = self._guess_audio_mime_type(user_audio_url)
        reference_mime = self._guess_audio_mime_type(reference_audio_url)

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=[
                    prompt,
                    types.Part.from_uri(file_uri=reference_audio_url, mime_type=reference_mime),
                    types.Part.from_uri(file_uri=user_audio_url, mime_type=user_mime),
                ],
                config=config,
            )
            return response.text or ""
        except Exception as uri_error:
            try:
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=[
                        prompt,
                        types.Part.from_bytes(
                            data=self._download_audio_bytes(reference_audio_url),
                            mime_type=reference_mime,
                        ),
                        types.Part.from_bytes(
                            data=self._download_audio_bytes(user_audio_url),
                            mime_type=user_mime,
                        ),
                    ],
                    config=config,
                )
                return response.text or ""
            except Exception as inline_error:
                raise AIFeedbackError(
                    "Gemini audio request failed. "
                    f"uri_mode_error={uri_error}; inline_mode_error={inline_error}"
                )

    def _generate_text_only(self, prompt: str, max_output_tokens: int) -> str:
        """Generate text-only response."""
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=max_output_tokens,
                    response_mime_type="application/json",
                ),
            )
            return response.text or ""
        except Exception as e:
            raise AIFeedbackError(str(e))

    @staticmethod
    def _normalize_suggestions(raw: Any) -> list[dict[str, Any]]:
        """Normalize suggestions to a stable list-of-objects schema."""
        if not isinstance(raw, list):
            raise AIFeedbackError("Field 'suggestions' must be a list")

        normalized: list[dict[str, Any]] = []
        for item in raw:
            if isinstance(item, str):
                normalized.append(
                    {"text": item, "target_word": None, "timestamp": None}
                )
                continue

            if not isinstance(item, dict):
                raise AIFeedbackError("Each suggestion must be an object or string")

            text = item.get("text")
            if not isinstance(text, str) or not text.strip():
                raise AIFeedbackError("Each suggestion requires a non-empty 'text'")

            target_word = item.get("target_word")
            if target_word is not None and not isinstance(target_word, str):
                raise AIFeedbackError("suggestion.target_word must be a string or null")

            timestamp = item.get("timestamp")
            if timestamp is not None and not isinstance(timestamp, (int, float)):
                raise AIFeedbackError("suggestion.timestamp must be a number or null")

            normalized.append(
                {
                    "text": text.strip(),
                    "target_word": target_word,
                    "timestamp": float(timestamp) if timestamp is not None else None,
                }
            )

        return normalized

    @staticmethod
    def _normalize_issues(raw: Any) -> list[dict[str, Any]]:
        """Normalize issues to [{problem, timestamp}] format."""
        if not isinstance(raw, list):
            raise AIFeedbackError("Field 'issues' must be a list")

        normalized: list[dict[str, Any]] = []
        for item in raw:
            if not isinstance(item, dict):
                raise AIFeedbackError("Each issue must be an object")

            problem = item.get("problem")
            if not isinstance(problem, str) or not problem.strip():
                raise AIFeedbackError("Each issue requires a non-empty 'problem'")

            timestamp = item.get("timestamp")
            if timestamp is not None and not isinstance(timestamp, (int, float)):
                raise AIFeedbackError("issue.timestamp must be a number or null")

            normalized.append(
                {
                    "problem": problem.strip(),
                    "timestamp": float(timestamp) if timestamp is not None else None,
                }
            )

        return normalized

    def generate_single_feedback(
        self,
        front_text: str,
        user_audio_url: str,
        reference_audio_url: str,
    ) -> dict[str, Any]:
        """Generate single-sentence feedback from user/reference audio."""
        try:
            prompt = self._render_prompt(
                self.single_feedback_prompt,
                original_text=front_text,
                user_audio_url=user_audio_url,
                reference_audio_url=reference_audio_url,
            )

            result_text = self._generate_with_audio(
                prompt=prompt,
                user_audio_url=user_audio_url,
                reference_audio_url=reference_audio_url,
                max_output_tokens=2048,
            )
            feedback = json.loads(self._extract_json_text(result_text))

            required_fields = [
                "pronunciation",
                "completeness",
                "fluency",
                "suggestions",
                "issues",
            ]
            for field in required_fields:
                if field not in feedback:
                    raise AIFeedbackError(f"Missing required field: {field}")

            for field in ("pronunciation", "completeness", "fluency"):
                if not isinstance(feedback[field], str):
                    raise AIFeedbackError(f"Field '{field}' must be a string")

            normalized_feedback = {
                "pronunciation": feedback["pronunciation"].strip(),
                "completeness": feedback["completeness"].strip(),
                "fluency": feedback["fluency"].strip(),
                "suggestions": self._normalize_suggestions(feedback["suggestions"]),
                "issues": self._normalize_issues(feedback["issues"]),
            }

            transcription_text = feedback.get("transcription_text")
            if transcription_text is not None:
                if not isinstance(transcription_text, str):
                    raise AIFeedbackError("Field 'transcription_text' must be a string")
                normalized_feedback["transcription_text"] = transcription_text.strip()

            return normalized_feedback

        except json.JSONDecodeError as e:
            raise AIFeedbackError(f"Failed to parse JSON response: {e}")
        except AIFeedbackError:
            raise
        except Exception as e:
            raise AIFeedbackError(str(e))

    def generate_lesson_summary(
        self,
        feedbacks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Generate lesson-level summary from all feedback."""
        try:
            feedbacks_json = json.dumps(feedbacks, ensure_ascii=False, indent=2)
            prompt = self._render_prompt(
                self.lesson_summary_prompt,
                feedbacks_json=feedbacks_json,
            )

            result_text = self._generate_text_only(prompt, max_output_tokens=2048)
            summary = json.loads(self._extract_json_text(result_text))

            required_fields = ["overall", "patterns", "prioritized_actions"]
            for field in required_fields:
                if field not in summary:
                    raise AIFeedbackError(f"Missing required field: {field}")

            if not isinstance(summary["overall"], str):
                raise AIFeedbackError("Field 'overall' must be a string")
            if not isinstance(summary["patterns"], list):
                raise AIFeedbackError("Field 'patterns' must be a list")
            if not isinstance(summary["prioritized_actions"], list):
                raise AIFeedbackError("Field 'prioritized_actions' must be a list")

            return summary

        except json.JSONDecodeError as e:
            raise AIFeedbackError(f"Failed to parse JSON response: {e}")
        except AIFeedbackError:
            raise
        except Exception as e:
            raise AIFeedbackError(str(e))
