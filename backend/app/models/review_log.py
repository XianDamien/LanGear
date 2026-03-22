"""Review log model for training records and AI feedback."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.utils.timezone import storage_now


class ReviewLog(Base):
    """Review log for training records and AI feedback.

    Stores both single-card feedback (result_type='single') and
    lesson summaries (result_type='summary').

    Supports asynchronous processing with status tracking.
    """

    __tablename__ = "review_log"

    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=True, index=True)  # NULL for summary
    deck_id = Column(Integer, ForeignKey("decks.id"), nullable=False, index=True)  # Lesson ID
    rating = Column(String(20), nullable=True)  # again/hard/good/easy (NULL for summary)
    result_type = Column(String(20), nullable=False, index=True)  # single/summary
    ai_feedback_json = Column(JSON, nullable=False)  # Stores AI feedback or summary

    # Asynchronous processing status
    status = Column(
        String(20), default="processing", nullable=False, index=True
    )  # processing/completed/failed
    error_code = Column(String(50), nullable=True)  # Error code if failed
    error_message = Column(Text, nullable=True)  # Error message if failed

    created_at = Column(DateTime, default=storage_now, nullable=False, index=True)

    # Relationships
    card = relationship("Card", back_populates="review_logs")
    deck = relationship("Deck")
