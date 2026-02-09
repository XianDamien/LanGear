"""User card SRS state model (FSRS scheduling)."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class UserCardSRS(Base):
    """FSRS scheduling state for each card.

    Stores the spaced repetition state calculated by FSRS algorithm.
    """

    __tablename__ = "user_card_srs"

    card_id = Column(Integer, ForeignKey("cards.id"), primary_key=True)
    state = Column(String(20), nullable=False, default="new")  # new/learning/review/relearning
    stability = Column(Float, nullable=False, default=0.0)  # FSRS stability parameter
    difficulty = Column(Float, nullable=False, default=0.0)  # FSRS difficulty parameter
    due = Column(DateTime, nullable=False, default=datetime.utcnow)  # Next review due time
    last_review = Column(DateTime, nullable=True)  # Last review timestamp
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    card = relationship("Card", back_populates="srs_state")
