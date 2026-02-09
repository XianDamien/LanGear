"""Google Gemini adapter for AI evaluation."""

import json
from pathlib import Path
from typing import Any

import google.generativeai as genai

from app.config import settings
from app.exceptions import AIFeedbackError


class GeminiAdapter:
    """Adapter for Google Gemini AI multimodal evaluation.

    Uses Gemini 2.5 Flash for generating:
    - Single-sentence feedback (pronunciation, completeness, fluency)
    - Lesson-level summaries (patterns, prioritized actions)
    """

    def __init__(self):
        """Initialize Gemini client with API key from settings."""
        # Configure API key
        genai.configure(api_key=settings.gemini_api_key)

        # Initialize model
        self.model_id = "gemini-2.0-flash-exp"
        self.model = genai.GenerativeModel(self.model_id)

        # Load prompt templates
        self.prompts_dir = Path(__file__).parent / "prompts"
        self.single_feedback_prompt = self._load_prompt("single_feedback.txt")
        self.lesson_summary_prompt = self._load_prompt("lesson_summary.txt")

    def _load_prompt(self, filename: str) -> str:
        """Load prompt template from file.

        Args:
            filename: Prompt template filename

        Returns:
            Prompt template content (empty string if file doesn't exist)
        """
        prompt_file = self.prompts_dir / filename
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8")
        return ""

    def _associate_timestamps(
        self, feedback: dict[str, Any], timestamps: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Associate timestamps with suggestions based on target_word.

        Args:
            feedback: Feedback dictionary with suggestions
            timestamps: Word-level timestamps from ASR

        Returns:
            Updated feedback with timestamps in suggestions
        """
        if not timestamps or "suggestions" not in feedback:
            return feedback

        # Create a word-to-timestamp mapping (case-insensitive)
        word_map = {
            item["word"].lower(): item["start"]
            for item in timestamps
            if "word" in item and "start" in item
        }

        # Associate timestamps with suggestions
        for suggestion in feedback.get("suggestions", []):
            target_word = suggestion.get("target_word")
            if target_word and isinstance(target_word, str):
                # Try to find matching timestamp
                target_lower = target_word.lower()
                if target_lower in word_map:
                    suggestion["timestamp"] = word_map[target_lower]

        return feedback

    def generate_single_feedback(
        self,
        front_text: str,
        transcription: str,
        timestamps: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Generate single-sentence feedback.

        Args:
            front_text: Original English text
            transcription: User's transcribed text from ASR
            timestamps: Optional word-level timestamps for targeted suggestions

        Returns:
            Feedback dictionary with:
            - pronunciation: Pronunciation assessment (text)
            - completeness: Content completeness assessment (text)
            - fluency: Fluency assessment (text)
            - suggestions: List of improvement suggestions with optional timestamps
                [{"text": str, "target_word": str|None, "timestamp": float|None}, ...]

        Raises:
            AIFeedbackError: If feedback generation fails
        """
        try:
            # Build prompt
            if self.single_feedback_prompt:
                # Use user-configured prompt
                prompt = self.single_feedback_prompt.format(
                    original_text=front_text,
                    user_transcription=transcription,
                )
            else:
                # Use default prompt
                prompt = f"""Evaluate the user's English speaking performance.

Original text: {front_text}
User's transcription: {transcription}

Please provide feedback in the following JSON format:
{{
  "pronunciation": "Assessment of pronunciation quality (text feedback only, no score)",
  "completeness": "Assessment of content completeness (text feedback only, no score)",
  "fluency": "Assessment of speaking fluency (text feedback only, no score)",
  "suggestions": [
    {{"text": "Suggestion 1", "target_word": "specific_word_if_applicable", "timestamp": null}},
    {{"text": "Suggestion 2", "target_word": null, "timestamp": null}},
    {{"text": "Suggestion 3", "target_word": null, "timestamp": null}}
  ]
}}

Note:
- Do NOT include any numerical scores
- Suggestions should include target_word if pointing to specific pronunciation issues
- Keep suggestions concise and actionable (max 3)

Return ONLY the JSON object, no other text."""

            # Generate content
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1024,
                ),
            )

            # Parse response
            result_text = response.text.strip()

            # Extract JSON from markdown code blocks if present
            if result_text.startswith("```"):
                # Remove markdown code block markers
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            feedback = json.loads(result_text)

            # Validate required fields
            required_fields = [
                "pronunciation",
                "completeness",
                "fluency",
                "suggestions",
            ]
            for field in required_fields:
                if field not in feedback:
                    raise AIFeedbackError(f"Missing required field: {field}")

            # Associate timestamps with suggestions if timestamps were provided
            if timestamps:
                feedback = self._associate_timestamps(feedback, timestamps)

            return feedback

        except json.JSONDecodeError as e:
            raise AIFeedbackError(f"Failed to parse JSON response: {str(e)}")
        except Exception as e:
            raise AIFeedbackError(str(e))

    def generate_lesson_summary(
        self,
        feedbacks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Generate lesson-level summary from all feedback.

        Args:
            feedbacks: List of all single-sentence feedback for the lesson

        Returns:
            Summary dictionary with:
            - overall: Overall performance assessment
            - patterns: List of recurring issue patterns (max 3)
            - prioritized_actions: List of prioritized improvement actions (max 3)

        Raises:
            AIFeedbackError: If summary generation fails
        """
        try:
            # Build prompt
            feedbacks_json = json.dumps(feedbacks, ensure_ascii=False, indent=2)

            if self.lesson_summary_prompt:
                # Use user-configured prompt
                prompt = self.lesson_summary_prompt.format(
                    feedbacks_json=feedbacks_json,
                )
            else:
                # Use default prompt
                prompt = f"""Analyze all feedback from this lesson and provide a summary.

All feedback:
{feedbacks_json}

Please provide a summary in the following JSON format:
{{
  "overall": "Overall performance assessment for this lesson",
  "patterns": ["Pattern 1", "Pattern 2", "Pattern 3"],
  "prioritized_actions": ["Action 1", "Action 2", "Action 3"]
}}

Return ONLY the JSON object, no other text."""

            # Generate content
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=2048,
                ),
            )

            # Parse response
            result_text = response.text.strip()

            # Extract JSON from markdown code blocks if present
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            summary = json.loads(result_text)

            # Validate required fields
            required_fields = ["overall", "patterns", "prioritized_actions"]
            for field in required_fields:
                if field not in summary:
                    raise AIFeedbackError(f"Missing required field: {field}")

            return summary

        except json.JSONDecodeError as e:
            raise AIFeedbackError(f"Failed to parse JSON response: {str(e)}")
        except Exception as e:
            raise AIFeedbackError(str(e))
