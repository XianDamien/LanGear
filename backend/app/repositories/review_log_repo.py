"""Review log repository for database operations."""

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.review_log import ReviewLog


class ReviewLogRepository:
    """Repository for ReviewLog model operations."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        self.db = db

    def create(
        self,
        deck_id: int,
        result_type: str,
        ai_feedback_json: dict[str, Any],
        card_id: int | None = None,
        rating: str | None = None,
    ) -> ReviewLog:
        """Create a review log entry.

        Args:
            deck_id: Lesson deck ID
            result_type: Type of result (single/summary)
            ai_feedback_json: AI feedback or summary JSON
            card_id: Card ID (None for summaries)
            rating: User rating (None for summaries)

        Returns:
            Created ReviewLog object
        """
        log = ReviewLog(
            card_id=card_id,
            deck_id=deck_id,
            rating=rating,
            result_type=result_type,
            ai_feedback_json=ai_feedback_json,
        )
        self.db.add(log)
        self.db.flush()
        return log

    def get_single_feedbacks_by_lesson(self, lesson_id: int) -> list[dict[str, Any]]:
        """Get all single-card feedback for a lesson.

        Args:
            lesson_id: Lesson deck ID

        Returns:
            List of feedback JSON objects
        """
        logs = (
            self.db.query(ReviewLog)
            .filter(
                ReviewLog.deck_id == lesson_id,
                ReviewLog.result_type == "single",
            )
            .all()
        )
        return [log.ai_feedback_json for log in logs]

    def get_summary_by_lesson(self, lesson_id: int) -> ReviewLog | None:
        """Get lesson summary if it exists.

        Args:
            lesson_id: Lesson deck ID

        Returns:
            ReviewLog object for summary or None
        """
        return (
            self.db.query(ReviewLog)
            .filter(
                ReviewLog.deck_id == lesson_id,
                ReviewLog.result_type == "summary",
            )
            .first()
        )

    def count_reviews_by_date(self, date: datetime) -> int:
        """Count reviews on a specific date.

        Args:
            date: Date to count reviews

        Returns:
            Number of reviews
        """
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(hour=23, minute=59, second=59, microsecond=999999)

        return (
            self.db.query(ReviewLog)
            .filter(
                ReviewLog.result_type == "single",
                ReviewLog.created_at >= start,
                ReviewLog.created_at <= end,
            )
            .count()
        )

    def get_latest_oss_paths_by_lesson(self, lesson_id: int) -> dict[int, str]:
        """Get the latest oss_audio_path for each card in a lesson.

        Args:
            lesson_id: Lesson deck ID

        Returns:
            Dictionary mapping card_id to oss_path string
        """
        from sqlalchemy import func

        # Subquery: latest completed review_log id per card
        subq = (
            self.db.query(
                ReviewLog.card_id,
                func.max(ReviewLog.id).label("max_id"),
            )
            .filter(
                ReviewLog.deck_id == lesson_id,
                ReviewLog.result_type == "single",
                ReviewLog.status == "completed",
                ReviewLog.card_id.isnot(None),
            )
            .group_by(ReviewLog.card_id)
            .subquery()
        )

        logs = (
            self.db.query(ReviewLog)
            .join(subq, ReviewLog.id == subq.c.max_id)
            .all()
        )

        result: dict[int, str] = {}
        for log in logs:
            if log.ai_feedback_json and log.ai_feedback_json.get("oss_path"):
                result[log.card_id] = log.ai_feedback_json["oss_path"]
        return result

    def get_by_id(self, log_id: int) -> ReviewLog | None:
        """Get review log by ID.

        Args:
            log_id: Review log ID

        Returns:
            ReviewLog object or None if not found
        """
        return self.db.query(ReviewLog).filter(ReviewLog.id == log_id).first()

    def update_status(
        self,
        log_id: int,
        status: str,
        ai_feedback_json: dict[str, Any] | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> ReviewLog | None:
        """Update review log status and optionally feedback.

        Args:
            log_id: Review log ID
            status: New status (processing/completed/failed)
            ai_feedback_json: Updated AI feedback (optional)
            error_code: Error code if failed (optional)
            error_message: Error message if failed (optional)

        Returns:
            Updated ReviewLog object or None if not found
        """
        log = self.get_by_id(log_id)
        if log is None:
            return None

        log.status = status

        if ai_feedback_json is not None:
            log.ai_feedback_json = ai_feedback_json

        if error_code is not None:
            log.error_code = error_code

        if error_message is not None:
            log.error_message = error_message

        self.db.flush()
        return log
