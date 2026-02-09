"""Background task for processing review submissions asynchronously."""

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.adapters.asr_adapter import ASRAdapter
from app.adapters.gemini_adapter import GeminiAdapter
from app.adapters.oss_adapter import OSSAdapter
from app.database import SessionLocal
from app.exceptions import AIFeedbackError, ASRTranscriptionError
from app.repositories.card_repo import CardRepository
from app.repositories.review_log_repo import ReviewLogRepository

logger = logging.getLogger(__name__)


def process_review_task(
    submission_id: int,
    card_id: int,
    lesson_id: int,
    oss_audio_path: str,
) -> None:
    """Process a single review submission asynchronously.

    This function runs in a background thread and handles:
    1. Generating OSS signed URL for audio
    2. ASR transcription with timestamps
    3. Gemini AI feedback generation
    4. Database updates (review_log)

    Note:
        FSRS scheduling is triggered by a separate rating submission step.

    Args:
        submission_id: Review log ID (submission ID)
        card_id: Card ID being reviewed
        lesson_id: Lesson deck ID
        oss_audio_path: OSS path to user's audio recording

    Returns:
        None (updates database directly)
    """
    db: Session = SessionLocal()

    try:
        logger.info(f"Processing review submission {submission_id}")

        # Initialize adapters
        oss_adapter = OSSAdapter()
        asr_adapter = ASRAdapter()
        gemini_adapter = GeminiAdapter()
        # Initialize repositories
        card_repo = CardRepository(db)
        review_log_repo = ReviewLogRepository(db)

        # Step 1: Generate OSS signed URL (1 hour expiration)
        logger.info(f"Generating signed URL for {oss_audio_path}")
        signed_url = oss_adapter.generate_signed_url(oss_audio_path, expires=3600)

        # Step 2: ASR transcription
        logger.info(f"Starting ASR transcription for submission {submission_id}")
        try:
            transcription_result = asr_adapter.transcribe(signed_url)
            transcription_text = transcription_result["text"]
            timestamps = transcription_result["timestamps"]
        except ASRTranscriptionError as e:
            logger.error(f"ASR failed for submission {submission_id}: {str(e)}")
            review_log_repo.update_status(
                log_id=submission_id,
                status="failed",
                error_code="ASR_TRANSCRIPTION_FAILED",
                error_message=str(e),
            )
            db.commit()
            return

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
