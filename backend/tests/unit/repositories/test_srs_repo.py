"""
Unit tests for SRSRepository.

Tests SRS repository operations including:
- Getting SRS state by card ID
- Upserting SRS state (INSERT and UPDATE)
- Counting due cards
- Counting completed cards
- FSRS state management
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.repositories.srs_repo import SRSRepository
from app.models.deck import Deck
from app.models.card import Card
from app.models.user_card_srs import UserCardSRS


@pytest.mark.unit
class TestSRSRepository:
    """Test SRSRepository operations."""

    def test_get_by_card_id_not_found(self, test_db: Session):
        """Test getting SRS state when it doesn't exist."""
        repo = SRSRepository(test_db)

        result = repo.get_by_card_id(99999)

        assert result is None

    def test_get_by_card_id_found(self, test_db: Session):
        """Test getting SRS state when it exists."""
        repo = SRSRepository(test_db)

        # Create lesson and card
        lesson = Deck(title="Lesson 1", type="lesson", level_index=0)
        test_db.add(lesson)
        test_db.flush()

        card = Card(deck_id=lesson.id, card_index=0, front_text="Test", back_text="测试")
        test_db.add(card)
        test_db.flush()

        # Create SRS state
        srs = UserCardSRS(
            card_id=card.id,
            state="new",
            stability=0.0,
            difficulty=5.0,
            due=datetime.utcnow()
        )
        test_db.add(srs)
        test_db.commit()

        # Get by card ID
        result = repo.get_by_card_id(card.id)

        assert result is not None
        assert result.card_id == card.id
        assert result.state == "new"
        assert result.stability == 0.0
        assert result.difficulty == 5.0

    def test_upsert_insert_new_state(self, test_db: Session):
        """Test upserting when SRS state doesn't exist (INSERT)."""
        repo = SRSRepository(test_db)

        # Create lesson and card
        lesson = Deck(title="Lesson 1", type="lesson", level_index=0)
        test_db.add(lesson)
        test_db.flush()

        card = Card(deck_id=lesson.id, card_index=0, front_text="Test", back_text="测试")
        test_db.add(card)
        test_db.commit()

        # Verify no SRS state exists
        assert repo.get_by_card_id(card.id) is None

        # Upsert new SRS state
        due_time = datetime.utcnow() + timedelta(days=1)
        srs = repo.upsert(
            card_id=card.id,
            state="learning",
            stability=1.5,
            difficulty=4.8,
            due=due_time
        )

        assert srs is not None
        assert srs.card_id == card.id
        assert srs.state == "learning"
        assert srs.stability == 1.5
        assert srs.difficulty == 4.8
        assert srs.due == due_time
        assert srs.last_review is not None

        # Verify it was persisted
        test_db.commit()
        result = repo.get_by_card_id(card.id)
        assert result.state == "learning"

    def test_upsert_update_existing_state(self, test_db: Session):
        """Test upserting when SRS state already exists (UPDATE)."""
        repo = SRSRepository(test_db)

        # Create lesson and card
        lesson = Deck(title="Lesson 1", type="lesson", level_index=0)
        test_db.add(lesson)
        test_db.flush()

        card = Card(deck_id=lesson.id, card_index=0, front_text="Test", back_text="测试")
        test_db.add(card)
        test_db.flush()

        # Create initial SRS state
        initial_due = datetime.utcnow()
        srs = UserCardSRS(
            card_id=card.id,
            state="new",
            stability=0.0,
            difficulty=5.0,
            due=initial_due
        )
        test_db.add(srs)
        test_db.commit()

        # Update via upsert
        new_due = datetime.utcnow() + timedelta(days=7)
        updated_srs = repo.upsert(
            card_id=card.id,
            state="review",
            stability=7.0,
            difficulty=4.0,
            due=new_due
        )

        assert updated_srs.card_id == card.id
        assert updated_srs.state == "review"
        assert updated_srs.stability == 7.0
        assert updated_srs.difficulty == 4.0
        assert updated_srs.due == new_due
        assert updated_srs.last_review is not None

        # Verify update was persisted
        test_db.commit()
        result = repo.get_by_card_id(card.id)
        assert result.state == "review"
        assert result.stability == 7.0

    def test_upsert_multiple_updates(self, test_db: Session):
        """Test upserting the same card multiple times."""
        repo = SRSRepository(test_db)

        # Create lesson and card
        lesson = Deck(title="Lesson 1", type="lesson", level_index=0)
        test_db.add(lesson)
        test_db.flush()

        card = Card(deck_id=lesson.id, card_index=0, front_text="Test", back_text="测试")
        test_db.add(card)
        test_db.commit()

        # First upsert - new
        repo.upsert(card.id, "new", 0.0, 5.0, datetime.utcnow())
        test_db.commit()
        assert repo.get_by_card_id(card.id).state == "new"

        # Second upsert - learning
        repo.upsert(card.id, "learning", 1.0, 5.0, datetime.utcnow() + timedelta(hours=10))
        test_db.commit()
        assert repo.get_by_card_id(card.id).state == "learning"

        # Third upsert - review
        repo.upsert(card.id, "review", 7.0, 4.5, datetime.utcnow() + timedelta(days=7))
        test_db.commit()
        srs = repo.get_by_card_id(card.id)
        assert srs.state == "review"
        assert srs.stability == 7.0
        assert srs.difficulty == 4.5

    def test_upsert_updates_last_review_time(self, test_db: Session):
        """Test that upsert always updates last_review timestamp."""
        repo = SRSRepository(test_db)

        # Create lesson and card
        lesson = Deck(title="Lesson 1", type="lesson", level_index=0)
        test_db.add(lesson)
        test_db.flush()

        card = Card(deck_id=lesson.id, card_index=0, front_text="Test", back_text="测试")
        test_db.add(card)
        test_db.commit()

        # First upsert
        before_time = datetime.utcnow()
        srs1 = repo.upsert(card.id, "new", 0.0, 5.0, datetime.utcnow())
        test_db.commit()

        assert srs1.last_review >= before_time

        # Wait a moment and upsert again
        import time
        time.sleep(0.1)  # Larger delay for reliability

        srs2 = repo.upsert(card.id, "learning", 1.0, 5.0, datetime.utcnow())
        test_db.commit()

        assert srs2.last_review >= srs1.last_review

    def test_count_due_by_lesson_empty(self, test_db: Session):
        """Test counting due cards when lesson has no cards."""
        repo = SRSRepository(test_db)

        # Create lesson without cards
        lesson = Deck(title="Empty Lesson", type="lesson", level_index=0)
        test_db.add(lesson)
        test_db.commit()

        count = repo.count_due_by_lesson(lesson.id)

        assert count == 0

    def test_count_due_by_lesson_no_due_cards(self, test_db: Session):
        """Test counting due cards when no cards are due."""
        repo = SRSRepository(test_db)

        # Create lesson and card
        lesson = Deck(title="Lesson 1", type="lesson", level_index=0)
        test_db.add(lesson)
        test_db.flush()

        card = Card(deck_id=lesson.id, card_index=0, front_text="Test", back_text="测试")
        test_db.add(card)
        test_db.flush()

        # Create SRS state with future due date
        future_due = datetime.utcnow() + timedelta(days=7)
        srs = UserCardSRS(
            card_id=card.id,
            state="review",
            stability=7.0,
            difficulty=5.0,
            due=future_due
        )
        test_db.add(srs)
        test_db.commit()

        count = repo.count_due_by_lesson(lesson.id)

        assert count == 0

    def test_count_due_by_lesson_with_due_cards(self, test_db: Session):
        """Test counting due cards when cards are due."""
        repo = SRSRepository(test_db)

        # Create lesson
        lesson = Deck(title="Lesson 1", type="lesson", level_index=0)
        test_db.add(lesson)
        test_db.flush()

        # Create cards with different due times
        now = datetime.utcnow()

        # Card 1 - due now
        card1 = Card(deck_id=lesson.id, card_index=0, front_text="Card 1", back_text="卡片1")
        test_db.add(card1)
        test_db.flush()
        srs1 = UserCardSRS(card_id=card1.id, state="review", stability=1.0, difficulty=5.0, due=now)
        test_db.add(srs1)

        # Card 2 - overdue
        card2 = Card(deck_id=lesson.id, card_index=1, front_text="Card 2", back_text="卡片2")
        test_db.add(card2)
        test_db.flush()
        srs2 = UserCardSRS(card_id=card2.id, state="review", stability=1.0, difficulty=5.0, due=now - timedelta(days=1))
        test_db.add(srs2)

        # Card 3 - not due yet
        card3 = Card(deck_id=lesson.id, card_index=2, front_text="Card 3", back_text="卡片3")
        test_db.add(card3)
        test_db.flush()
        srs3 = UserCardSRS(card_id=card3.id, state="review", stability=1.0, difficulty=5.0, due=now + timedelta(days=1))
        test_db.add(srs3)

        test_db.commit()

        count = repo.count_due_by_lesson(lesson.id)

        assert count == 2  # Only card1 and card2 are due

    def test_count_due_by_lesson_excludes_new_state(self, test_db: Session):
        """Test due counting excludes cards still in the pure-new state."""
        repo = SRSRepository(test_db)

        lesson = Deck(title="Lesson 1", type="lesson", level_index=0)
        test_db.add(lesson)
        test_db.flush()

        due_time = datetime.utcnow() - timedelta(hours=1)
        new_card = Card(deck_id=lesson.id, card_index=0, front_text="New card")
        review_card = Card(deck_id=lesson.id, card_index=1, front_text="Review card")
        test_db.add_all([new_card, review_card])
        test_db.flush()

        test_db.add_all(
            [
                UserCardSRS(
                    card_id=new_card.id,
                    state="new",
                    stability=0.0,
                    difficulty=5.0,
                    due=due_time,
                ),
                UserCardSRS(
                    card_id=review_card.id,
                    state="review",
                    stability=3.0,
                    difficulty=4.0,
                    due=due_time,
                ),
            ]
        )
        test_db.commit()

        assert repo.count_due_by_lesson(lesson.id) == 1

    def test_count_due_by_lesson_only_counts_correct_lesson(self, test_db: Session):
        """Test that count_due_by_lesson only counts cards from the specified lesson."""
        repo = SRSRepository(test_db)

        # Create two lessons
        lesson1 = Deck(title="Lesson 1", type="lesson", level_index=0)
        lesson2 = Deck(title="Lesson 2", type="lesson", level_index=1)
        test_db.add_all([lesson1, lesson2])
        test_db.flush()

        now = datetime.utcnow()

        # Create due cards in lesson1
        for i in range(3):
            card = Card(deck_id=lesson1.id, card_index=i, front_text=f"Card {i}")
            test_db.add(card)
            test_db.flush()
            srs = UserCardSRS(card_id=card.id, state="review", stability=1.0, difficulty=5.0, due=now)
            test_db.add(srs)

        # Create due cards in lesson2
        for i in range(2):
            card = Card(deck_id=lesson2.id, card_index=i, front_text=f"Card {i}")
            test_db.add(card)
            test_db.flush()
            srs = UserCardSRS(card_id=card.id, state="review", stability=1.0, difficulty=5.0, due=now)
            test_db.add(srs)

        test_db.commit()

        assert repo.count_due_by_lesson(lesson1.id) == 3
        assert repo.count_due_by_lesson(lesson2.id) == 2

    def test_count_completed_by_lesson_empty(self, test_db: Session):
        """Test counting completed cards when lesson has no cards."""
        repo = SRSRepository(test_db)

        # Create lesson without cards
        lesson = Deck(title="Empty Lesson", type="lesson", level_index=0)
        test_db.add(lesson)
        test_db.commit()

        count = repo.count_completed_by_lesson(lesson.id)

        assert count == 0

    def test_count_completed_by_lesson_no_reviewed_cards(self, test_db: Session):
        """Test counting completed cards when no cards have been reviewed."""
        repo = SRSRepository(test_db)

        # Create lesson with cards but no SRS states
        lesson = Deck(title="Lesson 1", type="lesson", level_index=0)
        test_db.add(lesson)
        test_db.flush()

        card = Card(deck_id=lesson.id, card_index=0, front_text="Test", back_text="测试")
        test_db.add(card)
        test_db.commit()

        count = repo.count_completed_by_lesson(lesson.id)

        assert count == 0

    def test_count_completed_by_lesson_with_reviewed_cards(self, test_db: Session):
        """Test counting completed cards when cards have been reviewed."""
        repo = SRSRepository(test_db)

        # Create lesson
        lesson = Deck(title="Lesson 1", type="lesson", level_index=0)
        test_db.add(lesson)
        test_db.flush()

        # Create cards with SRS states
        for i in range(5):
            card = Card(deck_id=lesson.id, card_index=i, front_text=f"Card {i}")
            test_db.add(card)
            test_db.flush()

            srs = UserCardSRS(
                card_id=card.id,
                state="review",
                stability=5.0,
                difficulty=5.0,
                due=datetime.utcnow() + timedelta(days=i)
            )
            test_db.add(srs)

        test_db.commit()

        count = repo.count_completed_by_lesson(lesson.id)

        assert count == 5

    def test_count_completed_by_lesson_only_counts_correct_lesson(self, test_db: Session):
        """Test that count_completed_by_lesson only counts cards from the specified lesson."""
        repo = SRSRepository(test_db)

        # Create two lessons
        lesson1 = Deck(title="Lesson 1", type="lesson", level_index=0)
        lesson2 = Deck(title="Lesson 2", type="lesson", level_index=1)
        test_db.add_all([lesson1, lesson2])
        test_db.flush()

        # Create reviewed cards in lesson1
        for i in range(7):
            card = Card(deck_id=lesson1.id, card_index=i, front_text=f"Card {i}")
            test_db.add(card)
            test_db.flush()
            srs = UserCardSRS(card_id=card.id, state="review", stability=1.0, difficulty=5.0, due=datetime.utcnow())
            test_db.add(srs)

        # Create reviewed cards in lesson2
        for i in range(4):
            card = Card(deck_id=lesson2.id, card_index=i, front_text=f"Card {i}")
            test_db.add(card)
            test_db.flush()
            srs = UserCardSRS(card_id=card.id, state="review", stability=1.0, difficulty=5.0, due=datetime.utcnow())
            test_db.add(srs)

        test_db.commit()

        assert repo.count_completed_by_lesson(lesson1.id) == 7
        assert repo.count_completed_by_lesson(lesson2.id) == 4

    def test_srs_state_transitions(self, test_db: Session):
        """Test SRS state transitions from new -> learning -> review."""
        repo = SRSRepository(test_db)

        # Create lesson and card
        lesson = Deck(title="Lesson 1", type="lesson", level_index=0)
        test_db.add(lesson)
        test_db.flush()

        card = Card(deck_id=lesson.id, card_index=0, front_text="Test", back_text="测试")
        test_db.add(card)
        test_db.commit()

        # State 1: new
        srs = repo.upsert(card.id, "new", 0.0, 5.0, datetime.utcnow())
        test_db.commit()
        assert srs.state == "new"

        # State 2: learning
        srs = repo.upsert(card.id, "learning", 1.0, 5.0, datetime.utcnow() + timedelta(hours=10))
        test_db.commit()
        assert srs.state == "learning"

        # State 3: review
        srs = repo.upsert(card.id, "review", 7.0, 4.5, datetime.utcnow() + timedelta(days=7))
        test_db.commit()
        assert srs.state == "review"
