"""Content service for deck tree and card queries."""

from typing import Any

from sqlalchemy.orm import Session

from app.repositories.card_repo import CardRepository
from app.repositories.deck_repo import DeckRepository
from app.repositories.srs_repo import SRSRepository


class ContentService:
    """Service for querying educational content (decks and cards)."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
        self.deck_repo = DeckRepository(db)
        self.card_repo = CardRepository(db)
        self.srs_repo = SRSRepository(db)

    def get_deck_tree(self) -> dict[str, Any]:
        """Get the complete deck tree: sources -> units -> lessons.

        Returns:
            Dictionary with:
            - sources: List of source decks with nested units and lessons
                Each lesson includes: total_cards, completed_cards, due_cards

        Example:
            {
                "sources": [
                    {
                        "id": 1,
                        "title": "New Concept English Book 2",
                        "units": [
                            {
                                "id": 11,
                                "title": "Unit 1",
                                "lessons": [
                                    {
                                        "id": 111,
                                        "title": "Lesson 1",
                                        "total_cards": 24,
                                        "completed_cards": 8,
                                        "due_cards": 5
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        """
        # Get all source decks (type='source')
        sources = self.deck_repo.get_all_sources()

        result_sources = []
        for source in sources:
            # Get units for this source
            units = self.deck_repo.get_children(source.id)

            result_units = []
            for unit in units:
                # Get lessons for this unit
                lessons = self.deck_repo.get_children(unit.id)

                result_lessons = []
                for lesson in lessons:
                    # Get statistics for this lesson
                    total_cards = self.card_repo.count_by_lesson(lesson.id)
                    completed_cards = self.srs_repo.count_completed_by_lesson(lesson.id)
                    due_cards = self.srs_repo.count_due_by_lesson(lesson.id)

                    result_lessons.append(
                        {
                            "id": lesson.id,
                            "title": lesson.title,
                            "total_cards": total_cards,
                            "completed_cards": completed_cards,
                            "due_cards": due_cards,
                        }
                    )

                result_units.append(
                    {
                        "id": unit.id,
                        "title": unit.title,
                        "lessons": result_lessons,
                    }
                )

            result_sources.append(
                {
                    "id": source.id,
                    "title": source.title,
                    "units": result_units,
                }
            )

        return {"sources": result_sources}

    def get_lesson_cards(self, lesson_id: int) -> dict[str, Any]:
        """Get all cards in a lesson (ordered by card_index).

        Args:
            lesson_id: Lesson deck ID

        Returns:
            Dictionary with:
            - lesson_id: Lesson ID
            - cards: List of card objects with id, card_index, front_text, back_text, audio_path

        Raises:
            ValueError: If lesson not found
        """
        # Verify lesson exists
        lesson = self.deck_repo.get_by_id(lesson_id)
        if not lesson or lesson.type != "lesson":
            raise ValueError(f"Lesson {lesson_id} not found")

        # Get all cards ordered by card_index
        cards = self.card_repo.get_by_lesson(lesson_id)

        result_cards = [
            {
                "id": card.id,
                "card_index": card.card_index,
                "front_text": card.front_text,
                "back_text": card.back_text,
                "audio_path": card.audio_path,
            }
            for card in cards
        ]

        return {
            "lesson_id": lesson_id,
            "cards": result_cards,
        }
