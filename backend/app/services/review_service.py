"""Review service for training submissions and results."""

import logging
import threading
from typing import Any

from sqlalchemy.orm import Session

from app.adapters.fsrs_adapter import FSRSAdapter
from app.repositories.card_repo import CardRepository
from app.repositories.review_log_repo import ReviewLogRepository
from app.repositories.srs_repo import SRSRepository
from app.tasks.review_task import process_review_task

logger = logging.getLogger(__name__)


class ReviewService:
    """Service for handling review submissions and results.

    Manages asynchronous training flow:
    1. Submit review (immediate return with submission_id)
    2. Background processing (ASR + AI + FSRS)
    3. Poll for results
    """

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
        self.card_repo = CardRepository(db)
        self.review_log_repo = ReviewLogRepository(db)
        self.srs_repo = SRSRepository(db)
        self.fsrs_adapter = FSRSAdapter()

    def submit_card_review(
        self,
        lesson_id: int,
        card_id: int,
        oss_audio_path: str,
    ) -> dict[str, Any]:
        """Submit a card feedback request (synchronous part).

        Creates a review_log record with status='processing' and
        launches a background task for asynchronous processing.

        Args:
            lesson_id: Lesson deck ID
            card_id: Card ID being reviewed
            oss_audio_path: OSS path to user's audio recording

        Returns:
            Dictionary with:
            - submission_id: Review log ID for polling
            - status: "processing"

        Raises:
            ValueError: If card not found, invalid lesson, or invalid OSS path
        """
        # Validate card and lesson
        card = self.card_repo.get_by_id(card_id)
        if not card:
            raise ValueError(f"Card {card_id} not found")

        if card.deck_id != lesson_id:
            raise ValueError(f"Card {card_id} does not belong to lesson {lesson_id}")

        # Validate OSS path format
        if not oss_audio_path.startswith("recordings/"):
            raise ValueError("Invalid OSS path. Must start with 'recordings/'")

        # Create review_log with status='processing'
        review_log = self.review_log_repo.create(
            card_id=card_id,
            deck_id=lesson_id,
            rating=None,
            result_type="single",
            ai_feedback_json={},  # Empty initially, will be filled by background task
        )

        # Commit to get the log ID
        self.db.commit()

        submission_id = review_log.id
        logger.info(f"Created review submission {submission_id} for card {card_id}")

        # Launch background task
        task_thread = threading.Thread(
            target=process_review_task,
            args=(submission_id, card_id, lesson_id, oss_audio_path),
            daemon=True,
        )
        task_thread.start()
        logger.info(f"Started background task for submission {submission_id}")

        return {
            "submission_id": submission_id,
            "status": "processing",
        }

    def submit_submission_rating(
        self,
        submission_id: int,
        rating: str,
    ) -> dict[str, Any]:
        """Submit rating for a previously created submission.

        Rating is decoupled from AI feedback generation. It only drives
        FSRS scheduling updates and learning statistics.

        Args:
            submission_id: Review log ID returned from submit_card_review
            rating: User rating (again/hard/good/easy)

        Returns:
            Dictionary with updated rating and SRS state.

        Raises:
            ValueError: If submission not found, invalid rating, or submission failed.
        """
        valid_ratings = ["again", "hard", "good", "easy"]
        if rating not in valid_ratings:
            raise ValueError(f"Invalid rating. Must be one of: {valid_ratings}")

        review_log = self.review_log_repo.get_by_id(submission_id)
        if not review_log:
            raise ValueError(f"Submission {submission_id} not found")

        if review_log.status == "failed":
            raise ValueError(f"Submission {submission_id} failed")

        if review_log.card_id is None:
            raise ValueError("Cannot submit rating for summary submission")

        current_srs = self.srs_repo.get_by_card_id(review_log.card_id)
        new_srs_data = self.fsrs_adapter.schedule_card(current_srs, rating)

        srs = self.srs_repo.upsert(
            card_id=review_log.card_id,
            state=new_srs_data["state"],
            stability=new_srs_data["stability"],
            difficulty=new_srs_data["difficulty"],
            due=new_srs_data["due"],
        )

        review_log.rating = rating
        self.db.commit()

        return {
            "submission_id": submission_id,
            "rating": rating,
            "srs": {
                "state": srs.state,
                "difficulty": srs.difficulty,
                "stability": srs.stability,
                "due": srs.due.isoformat(),
            },
        }

    def get_submission_result(self, submission_id: int) -> dict[str, Any]:
        """Get submission result (for polling).

        Args:
            submission_id: Review log ID from submit_card_review

        Returns:
            Dictionary with status and result data:
            - If processing: {submission_id, status: "processing"}
            - If failed: {submission_id, status: "failed", error_code, error_message}
            - If completed: {submission_id, status: "completed", transcription, feedback, srs}

        Raises:
            ValueError: If submission not found
        """
        review_log = self.review_log_repo.get_by_id(submission_id)
        if not review_log:
            raise ValueError(f"Submission {submission_id} not found")

        # Processing status
        if review_log.status == "processing":
            return {
                "submission_id": submission_id,
                "status": "processing",
            }

        # Failed status
        if review_log.status == "failed":
            return {
                "submission_id": submission_id,
                "status": "failed",
                "error_code": review_log.error_code,
                "error_message": review_log.error_message,
            }

        # Completed status
        if review_log.status == "completed":
            result = {
                "submission_id": submission_id,
                "status": "completed",
                "result_type": "single",
            }

            # Add transcription and feedback from ai_feedback_json
            if review_log.ai_feedback_json:
                result["transcription"] = review_log.ai_feedback_json.get("transcription", {})
                result["feedback"] = review_log.ai_feedback_json.get("feedback", {})
                result["oss_audio_path"] = review_log.ai_feedback_json.get("oss_path")

            # SRS is only returned after rating is submitted (decoupled flow)
            if review_log.rating and review_log.card_id is not None:
                srs = self.srs_repo.get_by_card_id(review_log.card_id)
                if srs:
                    result["srs"] = {
                        "state": srs.state,
                        "difficulty": srs.difficulty,
                        "stability": srs.stability,
                        "due": srs.due.isoformat(),
                    }

            return result

        # Unknown status (should not happen)
        return {
            "submission_id": submission_id,
            "status": review_log.status,
        }
