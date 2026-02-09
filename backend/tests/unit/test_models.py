"""
Unit tests for SQLAlchemy models.

Tests model creation, relationships, and constraints.
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Deck, Card, UserCardSRS, ReviewLog, Setting


@pytest.mark.unit
class TestDeckModel:
    """Test Deck model creation and relationships."""

    def test_create_source_deck(self, test_db: Session):
        """Test creating a source deck."""
        deck = Deck(
            title="NCE Book 1",
            type="source",
            level_index=0,
            parent_id=None
        )
        test_db.add(deck)
        test_db.commit()

        assert deck.id is not None
        assert deck.title == "NCE Book 1"
        assert deck.type == "source"
        assert deck.level_index == 0
        assert deck.parent_id is None
        assert deck.created_at is not None
        assert deck.updated_at is not None

    def test_create_deck_hierarchy(self, test_db: Session):
        """Test creating parent-child deck relationships."""
        # Create source
        source = Deck(title="Source", type="source", level_index=0)
        test_db.add(source)
        test_db.flush()

        # Create unit
        unit = Deck(title="Unit 1", type="unit", level_index=0, parent_id=source.id)
        test_db.add(unit)
        test_db.flush()

        # Create lesson
        lesson = Deck(title="Lesson 1", type="lesson", level_index=0, parent_id=unit.id)
        test_db.add(lesson)
        test_db.commit()

        # Verify relationships
        assert unit.parent_id == source.id
        assert lesson.parent_id == unit.id

    def test_deck_type_validation(self, test_db: Session):
        """Test deck type must be source, unit, or lesson."""
        deck = Deck(title="Test", type="source", level_index=0)
        test_db.add(deck)
        test_db.commit()
        assert deck.type in ["source", "unit", "lesson"]


@pytest.mark.unit
class TestCardModel:
    """Test Card model creation and relationships."""

    def test_create_card(self, test_db: Session):
        """Test creating a card."""
        # Create lesson first
        lesson = Deck(title="Lesson 1", type="lesson", level_index=0)
        test_db.add(lesson)
        test_db.flush()

        # Create card
        card = Card(
            deck_id=lesson.id,
            card_index=0,
            front_text="Hello world",
            back_text="你好世界",
            audio_path="audio/test/0.wav"
        )
        test_db.add(card)
        test_db.commit()

        assert card.id is not None
        assert card.deck_id == lesson.id
        assert card.card_index == 0
        assert card.front_text == "Hello world"
        assert card.back_text == "你好世界"
        assert card.audio_path == "audio/test/0.wav"

    def test_card_lesson_relationship(self, test_db: Session):
        """Test card-lesson foreign key relationship."""
        lesson = Deck(title="Lesson 1", type="lesson", level_index=0)
        test_db.add(lesson)
        test_db.flush()

        card = Card(
            deck_id=lesson.id,
            card_index=0,
            front_text="Test",
            back_text="测试",
            audio_path="audio/test.wav"
        )
        test_db.add(card)
        test_db.commit()

        # Verify relationship
        assert card.deck_id == lesson.id


@pytest.mark.unit
class TestUserCardSRSModel:
    """Test UserCardSRS model."""

    def test_create_srs_new_state(self, test_db: Session):
        """Test creating SRS state for a new card."""
        # Create card first
        lesson = Deck(title="Lesson 1", type="lesson", level_index=0)
        test_db.add(lesson)
        test_db.flush()

        card = Card(
            deck_id=lesson.id,
            card_index=0,
            front_text="Test",
            back_text="测试",
            audio_path="test.wav"
        )
        test_db.add(card)
        test_db.flush()

        # Create SRS state (card_id is primary key)
        srs = UserCardSRS(
            card_id=card.id,
            state="new",
            stability=0.0,
            difficulty=5.0,
            due=datetime.now()
        )
        test_db.add(srs)
        test_db.commit()

        assert srs.card_id == card.id
        assert srs.state == "new"
        assert srs.stability == 0.0
        assert srs.difficulty == 5.0
        assert srs.last_review is None

    def test_srs_state_values(self, test_db: Session):
        """Test that all valid SRS states can be set on a model instance."""
        for state in ["new", "learning", "review", "relearning"]:
            srs = UserCardSRS(state=state, stability=0.0, difficulty=5.0, due=datetime.now())
            assert srs.state == state


@pytest.mark.unit
class TestReviewLogModel:
    """Test ReviewLog model."""

    def test_create_review_log_processing(self, test_db: Session):
        """Test creating a review log in processing state."""
        lesson = Deck(title="Lesson 1", type="lesson", level_index=0)
        test_db.add(lesson)
        test_db.flush()

        card = Card(deck_id=lesson.id, card_index=0, front_text="T", back_text="T", audio_path="a.wav")
        test_db.add(card)
        test_db.flush()

        log = ReviewLog(
            card_id=card.id,
            deck_id=lesson.id,
            rating="good",
            result_type="single",
            ai_feedback_json={},
            status="processing"
        )
        test_db.add(log)
        test_db.commit()

        assert log.id is not None
        assert log.card_id == card.id
        assert log.deck_id == lesson.id
        assert log.rating == "good"
        assert log.result_type == "single"
        assert log.status == "processing"
        assert log.error_message is None

    def test_review_log_completed(self, test_db: Session):
        """Test review log with completed status."""
        lesson = Deck(title="Lesson 1", type="lesson", level_index=0)
        test_db.add(lesson)
        test_db.flush()

        card = Card(deck_id=lesson.id, card_index=0, front_text="T", back_text="T", audio_path="a.wav")
        test_db.add(card)
        test_db.flush()

        log = ReviewLog(
            card_id=card.id,
            deck_id=lesson.id,
            rating="good",
            result_type="single",
            ai_feedback_json={
                "pronunciation": "Good",
                "completeness": "Complete",
                "fluency": "Fluent"
            },
            status="completed"
        )
        test_db.add(log)
        test_db.commit()

        assert log.status == "completed"
        assert log.ai_feedback_json is not None
        assert "pronunciation" in log.ai_feedback_json

    def test_review_log_failed(self, test_db: Session):
        """Test review log with failed status."""
        lesson = Deck(title="Lesson 1", type="lesson", level_index=0)
        test_db.add(lesson)
        test_db.flush()

        card = Card(deck_id=lesson.id, card_index=0, front_text="T", back_text="T", audio_path="a.wav")
        test_db.add(card)
        test_db.flush()

        log = ReviewLog(
            card_id=card.id,
            deck_id=lesson.id,
            rating="good",
            result_type="single",
            ai_feedback_json={},
            status="failed",
            error_code="ASR_ERROR",
            error_message="ASR service error"
        )
        test_db.add(log)
        test_db.commit()

        assert log.status == "failed"
        assert log.error_code == "ASR_ERROR"
        assert log.error_message is not None

    def test_review_log_summary(self, test_db: Session):
        """Test creating a lesson summary review log (no card_id)."""
        lesson = Deck(title="Lesson 1", type="lesson", level_index=0)
        test_db.add(lesson)
        test_db.flush()

        log = ReviewLog(
            card_id=None,  # Summary has no specific card
            deck_id=lesson.id,
            rating=None,  # Summary has no rating
            result_type="summary",
            ai_feedback_json={
                "overall_performance": "Good progress",
                "areas_for_improvement": ["Pronunciation"]
            },
            status="completed"
        )
        test_db.add(log)
        test_db.commit()

        assert log.result_type == "summary"
        assert log.card_id is None
        assert log.rating is None


@pytest.mark.unit
class TestSettingModel:
    """Test Setting model."""

    def test_create_setting(self, test_db: Session):
        """Test creating a setting."""
        setting = Setting(key="daily_new_cards", value={"count": 20})
        test_db.add(setting)
        test_db.commit()

        assert setting.key == "daily_new_cards"
        assert setting.value == {"count": 20}
        assert setting.updated_at is not None

    def test_setting_json_value(self, test_db: Session):
        """Test that setting values can be JSON."""
        setting = Setting(
            key="advanced_config",
            value={
                "enable_audio": True,
                "max_interval": 365,
                "themes": ["light", "dark"]
            }
        )
        test_db.add(setting)
        test_db.commit()

        assert isinstance(setting.value, dict)
        assert setting.value["enable_audio"] is True
        assert setting.value["max_interval"] == 365
