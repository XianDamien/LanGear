"""Study router for training submissions and results."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.review_service import ReviewService

router = APIRouter(prefix="/api/v1/study", tags=["Study"])


class SubmissionRequest(BaseModel):
    """Request model for submitting a card review."""

    lesson_id: int
    card_id: int
    rating: str  # again/hard/good/easy
    oss_audio_path: str


@router.post("/submissions")
def submit_review(
    request: SubmissionRequest,
    db: Session = Depends(get_db),
):
    """Submit a card review (asynchronous - returns immediately).

    Frontend flow:
    1. Upload audio to OSS using STS credentials
    2. Call this endpoint with OSS path
    3. Poll /submissions/{id} for result

    Args:
        request: Submission request with lesson_id, card_id, rating, oss_audio_path

    Returns:
        Response with submission ID:
        - request_id: Unique request ID
        - data:
            - submission_id: ID for polling results
            - status: "processing"

    Raises:
        400: If invalid rating or OSS path
        404: If card not found or invalid lesson
    """
    request_id = str(uuid.uuid4())

    try:
        review_service = ReviewService(db)
        result = review_service.submit_card_review(
            lesson_id=request.lesson_id,
            card_id=request.card_id,
            rating=request.rating,
            oss_audio_path=request.oss_audio_path,
        )

        return {
            "request_id": request_id,
            "data": result,
        }

    except ValueError as e:
        error_message = str(e)

        # Determine error code
        if "rating" in error_message.lower():
            error_code = "INVALID_RATING"
        elif "oss" in error_message.lower():
            error_code = "INVALID_OSS_PATH"
        elif "not found" in error_message.lower():
            error_code = "CARD_NOT_FOUND"
        else:
            error_code = "INVALID_REQUEST"

        raise HTTPException(
            status_code=400,
            detail={
                "request_id": request_id,
                "error": {
                    "code": error_code,
                    "message": error_message,
                },
            },
        )


@router.get("/submissions/{submission_id}")
def get_submission_result(
    submission_id: int,
    db: Session = Depends(get_db),
):
    """Poll for submission result (for frontend polling).

    Frontend should poll this endpoint every 1-2 seconds after submission.
    Recommended timeout: 30 seconds (stop polling but don't block user).

    Args:
        submission_id: Submission ID from submit_review

    Returns:
        Response with submission status and results:
        - request_id: Unique request ID
        - data:
            - submission_id: Submission ID
            - status: "processing" | "completed" | "failed"
            - [if completed]: transcription, feedback, srs
            - [if failed]: error_code, error_message

    Raises:
        404: If submission not found
    """
    request_id = str(uuid.uuid4())

    try:
        review_service = ReviewService(db)
        result = review_service.get_submission_result(submission_id)

        return {
            "request_id": request_id,
            "data": result,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "request_id": request_id,
                "error": {
                    "code": "SUBMISSION_NOT_FOUND",
                    "message": str(e),
                },
            },
        )
