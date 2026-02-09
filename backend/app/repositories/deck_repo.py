"""Deck repository for database operations."""

from sqlalchemy.orm import Session

from app.models.deck import Deck


class DeckRepository:
    """Repository for Deck model operations."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        self.db = db

    def get_all_sources(self) -> list[Deck]:
        """Get all top-level sources.

        Returns:
            List of Deck objects with type='source'
        """
        return (
            self.db.query(Deck)
            .filter(Deck.type == "source", Deck.parent_id.is_(None))
            .order_by(Deck.level_index)
            .all()
        )

    def get_children(self, parent_id: int) -> list[Deck]:
        """Get all children of a deck.

        Args:
            parent_id: Parent deck ID

        Returns:
            List of child Deck objects ordered by level_index
        """
        return (
            self.db.query(Deck)
            .filter(Deck.parent_id == parent_id)
            .order_by(Deck.level_index)
            .all()
        )

    def get_by_id(self, deck_id: int) -> Deck | None:
        """Get deck by ID.

        Args:
            deck_id: Deck ID

        Returns:
            Deck object or None if not found
        """
        return self.db.query(Deck).filter(Deck.id == deck_id).first()

    def create(
        self,
        title: str,
        type: str,
        parent_id: int | None = None,
        level_index: int = 0,
    ) -> Deck:
        """Create a new deck.

        Args:
            title: Deck title
            type: Deck type (source/unit/lesson)
            parent_id: Parent deck ID (None for sources)
            level_index: Sort order within parent

        Returns:
            Created Deck object
        """
        deck = Deck(
            title=title,
            type=type,
            parent_id=parent_id,
            level_index=level_index,
        )
        self.db.add(deck)
        self.db.flush()
        return deck
