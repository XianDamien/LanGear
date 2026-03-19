"""Background task for processing review submissions asynchronously."""

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.adapters.gemini_adapter import GeminiAdapter
from app.adapters.oss_adapter import OSSAdapter
from app.database import SessionLocal
from app.exceptions import AIFeedbackError
from app.repositories.card_repo import CardRepository
from app.repositories.review_log_repo import ReviewLogRepository

logger = logging.getLogger(__name__)


def process_review_task(
    submission_id: int,
    card_id: int,
    lesson_id: int,
    oss_audio_path: str,
    realtime_session_id: str,
    realtime_final_text: str,
) -> None:
    """Process a single review submission asynchronously.

    This function runs in a background thread and handles:
    1. Generating OSS signed URL for audio
    2. Gemini AI feedback generation (using realtime final transcript)
    4. Database updates (review_log)

    Note:
        FSRS scheduling is triggered by a separate rating submission step.

    Args:
        submission_id: Review log ID (submission ID)
        card_id: Card ID being reviewed
        lesson_id: Lesson deck ID
        oss_audio_path: OSS path to user's audio recording
        realtime_session_id: Realtime ASR session id
        realtime_final_text: Realtime ASR final transcript text

    Returns:
        None (updates database directly)
    """
    db: Session = SessionLocal()

    try:
        logger.info(f"Processing review submission {submission_id}")

        # Initialize adapters
        oss_adapter = OSSAdapter()
        gemini_adapter = GeminiAdapter()
        # Initialize repositories
        card_repo = CardRepository(db)
        review_log_repo = ReviewLogRepository(db)

        # Step 1: Generate OSS signed URL (1 hour expiration)
        logger.info(f"Generating signed URL for {oss_audio_path}")
        signed_url = oss_adapter.generate_signed_url(oss_audio_path, expires=3600)

        # Step 2: Use realtime final transcript from WS session
        transcription_text = realtime_final_text.strip()
        if not transcription_text:
            review_log_repo.update_status(
                log_id=submission_id,
                status="failed",
                error_code="REALTIME_TRANSCRIPT_NOT_READY",
                error_message="Realtime final transcript is empty",
            )
            db.commit()
            return
        timestamps = _build_word_timestamps(transcription_text)

        # Step 3: Get card original text
        card = card_repo.get_by_id(card_id)
        if not card:
            logger.error(f"Card {card_id} not found for submission {submission_id}")
            review_log_repo.update_status(
                log_id=submission_id,
                status="failed",
                error_code="CARD_NOT_FOUND",
                error_message=f"Card {card_id} not found",
            )
            db.commit()
            return

        # Step 4: Gemini AI feedback
        logger.info(f"Generating AI feedback for submission {submission_id}")
        try:
            feedback = gemini_adapter.generate_single_feedback(
                front_text=card.front_text,
                transcription=transcription_text,
                timestamps=timestamps,
            )
        except AIFeedbackError as e:
            logger.error(f"AI feedback failed for submission {submission_id}: {str(e)}")
            review_log_repo.update_status(
                log_id=submission_id,
                status="failed",
                error_code="AI_FEEDBACK_FAILED",
                error_message=str(e),
            )
            db.commit()
            return

        # Step 5: Update review_log with completed status
        logger.info(f"Finalizing submission {submission_id}")
        ai_feedback_json: dict[str, Any] = {
            "transcription": {
                "text": transcription_text,
                "timestamps": timestamps,
            },
            "feedback": feedback,
            "oss_path": oss_audio_path,
            "realtime_session_id": realtime_session_id,
            "audio_signed_url": signed_url,
        }

        review_log_repo.update_status(
            log_id=submission_id,
            status="completed",
            ai_feedback_json=ai_feedback_json,
        )

        # Commit all changes
        db.commit()
        logger.info(f"Successfully completed submission {submission_id}")

    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error in submission {submission_id}: {str(e)}", exc_info=True)
        try:
            review_log_repo = ReviewLogRepository(db)
            review_log_repo.update_status(
                log_id=submission_id,
                status="failed",
                error_code="UNEXPECTED_ERROR",
                error_message=str(e),
            )
            db.commit()
        except Exception as commit_error:
            logger.error(f"Failed to update error status: {str(commit_error)}")
            db.rollback()

    finally:
        db.close()


def _build_word_timestamps(text: str) -> list[dict[str, float | str]]:
    """Build lightweight pseudo word timestamps for clickable feedback."""
    words = text.split()
    if not words:
        return []

    timestamps: list[dict[str, float | str]] = []
    cursor = 0.0
    for word in words:
        duration = max(0.12, min(0.65, len(word) * 0.05))
        start = round(cursor, 3)
        end = round(cursor + duration, 3)
        timestamps.append({"word": word, "start": start, "end": end})
        cursor = end + 0.02
    return timestamps
