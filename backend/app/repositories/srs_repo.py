"""SRS repository for database operations."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.user_card_srs import UserCardSRS
from app.utils.timezone import to_storage_utc, utc_now_naive


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
                due=to_storage_utc(due),
                last_review=utc_now_naive(),
            )
            self.db.add(srs)
        else:
            # Update existing SRS state
            srs.state = state
            srs.stability = stability
            srs.difficulty = difficulty
            srs.due = to_storage_utc(due)
            srs.last_review = utc_now_naive()

        self.db.flush()
        return srs

    def count_due_by_lesson(self, lesson_id: int) -> int:
        """Count cards due for review in a lesson.

        Args:
            lesson_id: Lesson deck ID

        Returns:
            Number of cards due for review
        """
        return self.count_due_cards(lesson_ids=[lesson_id])

    def get_due_cards(
        self,
        lesson_ids: list[int] | None = None,
        states: list[str] | None = None,
        limit: int | None = None,
        as_of=None,
    ) -> list[tuple["Card", UserCardSRS]]:
        """Get due non-new cards joined with their card records."""
        from app.models.card import Card

        now = as_of if as_of is not None else utc_now_naive()
        query = (
            self.db.query(Card, UserCardSRS)
            .join(UserCardSRS, UserCardSRS.card_id == Card.id)
            .filter(
                UserCardSRS.due <= now,
                UserCardSRS.state != "new",
            )
            .order_by(UserCardSRS.due, Card.deck_id, Card.card_index, Card.id)
        )

        if lesson_ids is not None:
            if not lesson_ids:
                return []
            query = query.filter(Card.deck_id.in_(lesson_ids))

        if states is not None:
            if not states:
                return []
            query = query.filter(UserCardSRS.state.in_(states))

        if limit is not None:
            query = query.limit(limit)

        return query.all()

    def count_due_cards(
        self,
        lesson_ids: list[int] | None = None,
        states: list[str] | None = None,
        as_of=None,
    ) -> int:
        """Count due cards while excluding pure-new states."""
        from app.models.card import Card

        now = as_of if as_of is not None else utc_now_naive()
        query = (
            self.db.query(UserCardSRS)
            .join(Card, Card.id == UserCardSRS.card_id)
            .filter(
                UserCardSRS.due <= now,
                UserCardSRS.state != "new",
            )
        )

        if lesson_ids is not None:
            if not lesson_ids:
                return 0
            query = query.filter(Card.deck_id.in_(lesson_ids))

        if states is not None:
            if not states:
                return 0
            query = query.filter(UserCardSRS.state.in_(states))

        return query.count()

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
