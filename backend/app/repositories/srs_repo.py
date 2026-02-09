"""SRS repository for database operations."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.user_card_srs import UserCardSRS


class SRSRepository:
    """Repository for UserCardSRS model operations."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        self.db = db

    def get_by_card_id(self, card_id: int) -> UserCardSRS | None:
        """Get SRS state for a card.

        Args:
            card_id: Card ID

        Returns:
            UserCardSRS object or None if not exists
        """
        return (
            self.db.query(UserCardSRS)
            .filter(UserCardSRS.card_id == card_id)
            .first()
        )

    def upsert(
        self,
        card_id: int,
        state: str,
        stability: float,
        difficulty: float,
        due: datetime,
    ) -> UserCardSRS:
        """Create or update SRS state for a card.

        Args:
            card_id: Card ID
            state: FSRS state (new/learning/review/relearning)
            stability: FSRS stability parameter
            difficulty: FSRS difficulty parameter
            due: Next review due time

        Returns:
            UserCardSRS object
        """
        srs = self.get_by_card_id(card_id)

        if srs is None:
            # Create new SRS state
            srs = UserCardSRS(
                card_id=card_id,
                state=state,
                stability=stability,
                difficulty=difficulty,
                due=due,
                last_review=datetime.utcnow(),
            )
            self.db.add(srs)
        else:
            # Update existing SRS state
            srs.state = state
            srs.stability = stability
            srs.difficulty = difficulty
            srs.due = due
            srs.last_review = datetime.utcnow()

        self.db.flush()
        return srs

    def count_due_by_lesson(self, lesson_id: int) -> int:
        """Count cards due for review in a lesson.

        Args:
            lesson_id: Lesson deck ID

        Returns:
            Number of cards due for review
        """
        from app.models.card import Card

        now = datetime.utcnow()
        return (
            self.db.query(UserCardSRS)
            .join(Card, Card.id == UserCardSRS.card_id)
            .filter(Card.deck_id == lesson_id, UserCardSRS.due <= now)
            .count()
        )

    def count_completed_by_lesson(self, lesson_id: int) -> int:
        """Count cards that have been reviewed at least once.

        Args:
            lesson_id: Lesson deck ID

        Returns:
            Number of cards with SRS state (reviewed at least once)
        """
        from app.models.card import Card

        return (
            self.db.query(UserCardSRS)
            .join(Card, Card.id == UserCardSRS.card_id)
            .filter(Card.deck_id == lesson_id)
            .count()
        )
