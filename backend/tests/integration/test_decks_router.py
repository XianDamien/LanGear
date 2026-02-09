"""
Integration tests for decks and cards API endpoints.

Tests:
- GET /api/v1/decks/tree - Deck tree retrieval
- GET /api/v1/decks/{lesson_id}/cards - Lesson cards retrieval
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.mark.integration
class TestDecksRouter:
    """Test suite for decks and cards API endpoints."""

    # GET /api/v1/decks/tree tests

    def test_get_deck_tree_success(self, client: TestClient, test_db: Session, sample_deck_tree):
        """Test GET /api/v1/decks/tree returns successful response."""
        # Act
        response = client.get("/api/v1/decks/tree")

        # Assert
        assert response.status_code == 200

    def test_get_deck_tree_response_structure(self, client: TestClient, test_db: Session, sample_deck_tree):
        """Test GET /api/v1/decks/tree returns correct response structure."""
        # Act
        response = client.get("/api/v1/decks/tree")

        # Assert
        data = response.json()
        assert "request_id" in data
        assert "data" in data
        assert isinstance(data["request_id"], str)
        assert isinstance(data["data"], dict)

    def test_get_deck_tree_includes_request_id(self, client: TestClient, test_db: Session, sample_deck_tree):
        """Test GET /api/v1/decks/tree includes valid request_id."""
        # Act
        response = client.get("/api/v1/decks/tree")

        # Assert
        data = response.json()
        request_id = data["request_id"]
        assert len(request_id) > 0
        # Request ID should be a UUID
        assert "-" in request_id

    def test_get_deck_tree_data_structure(self, client: TestClient, test_db: Session, sample_deck_tree):
        """Test GET /api/v1/decks/tree returns proper deck tree structure."""
        # Act
        response = client.get("/api/v1/decks/tree")

        # Assert
        data = response.json()["data"]
        assert "sources" in data
        assert isinstance(data["sources"], list)

    def test_get_deck_tree_complete_hierarchy(self, client: TestClient, test_db: Session, sample_deck_tree):
        """Test GET /api/v1/decks/tree returns complete source->unit->lesson hierarchy."""
        # Act
        response = client.get("/api/v1/decks/tree")

        # Assert
        data = response.json()["data"]
        sources = data["sources"]

        assert len(sources) == 1
        source = sources[0]
        assert source["id"] == sample_deck_tree["source"].id
        assert source["title"] == "New Concept English Book 2"
        assert "units" in source

        units = source["units"]
        assert len(units) == 1
        unit = units[0]
        assert unit["id"] == sample_deck_tree["unit"].id
        assert "lessons" in unit

        lessons = unit["lessons"]
        assert len(lessons) == 1
        lesson = lessons[0]
        assert lesson["id"] == sample_deck_tree["lesson"].id

    def test_get_deck_tree_lesson_statistics(self, client: TestClient, test_db: Session, sample_deck_tree):
        """Test GET /api/v1/decks/tree includes lesson statistics."""
        # Act
        response = client.get("/api/v1/decks/tree")

        # Assert
        data = response.json()["data"]
        lesson = data["sources"][0]["units"][0]["lessons"][0]

        assert "total_cards" in lesson
        assert "completed_cards" in lesson
        assert "due_cards" in lesson
        assert lesson["total_cards"] == 5
        assert lesson["completed_cards"] == 5  # All cards have SRS state from seed data
        assert lesson["due_cards"] == 5

    def test_get_deck_tree_empty_database(self, client: TestClient, test_db: Session):
        """Test GET /api/v1/decks/tree returns empty sources when no decks exist."""
        # Act
        response = client.get("/api/v1/decks/tree")

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["sources"] == []

    def test_get_deck_tree_multiple_sources(self, client: TestClient, test_db: Session):
        """Test GET /api/v1/decks/tree handles multiple source decks."""
        # Arrange
        from app.models import Deck

        source1 = Deck(title="Source 1", type="source", level_index=0)
        source2 = Deck(title="Source 2", type="source", level_index=1)
        test_db.add_all([source1, source2])
        test_db.commit()

        # Act
        response = client.get("/api/v1/decks/tree")

        # Assert
        data = response.json()["data"]
        assert len(data["sources"]) == 2

    # GET /api/v1/decks/{lesson_id}/cards tests

    def test_get_lesson_cards_success(self, client: TestClient, test_db: Session, sample_deck_tree):
        """Test GET /api/v1/decks/{lesson_id}/cards returns successful response."""
        # Arrange
        lesson_id = sample_deck_tree["lesson"].id

        # Act
        response = client.get(f"/api/v1/decks/{lesson_id}/cards")

        # Assert
        assert response.status_code == 200

    def test_get_lesson_cards_response_structure(self, client: TestClient, test_db: Session, sample_deck_tree):
        """Test GET /api/v1/decks/{lesson_id}/cards returns correct response structure."""
        # Arrange
        lesson_id = sample_deck_tree["lesson"].id

        # Act
        response = client.get(f"/api/v1/decks/{lesson_id}/cards")

        # Assert
        data = response.json()
        assert "request_id" in data
        assert "data" in data
        assert isinstance(data["request_id"], str)
        assert isinstance(data["data"], dict)

    def test_get_lesson_cards_data_structure(self, client: TestClient, test_db: Session, sample_deck_tree):
        """Test GET /api/v1/decks/{lesson_id}/cards returns proper cards data structure."""
        # Arrange
        lesson_id = sample_deck_tree["lesson"].id

        # Act
        response = client.get(f"/api/v1/decks/{lesson_id}/cards")

        # Assert
        data = response.json()["data"]
        assert "lesson_id" in data
        assert "cards" in data
        assert data["lesson_id"] == lesson_id
        assert isinstance(data["cards"], list)

    def test_get_lesson_cards_returns_all_cards(self, client: TestClient, test_db: Session, sample_deck_tree):
        """Test GET /api/v1/decks/{lesson_id}/cards returns all cards in lesson."""
        # Arrange
        lesson_id = sample_deck_tree["lesson"].id

        # Act
        response = client.get(f"/api/v1/decks/{lesson_id}/cards")

        # Assert
        data = response.json()["data"]
        cards = data["cards"]
        assert len(cards) == 5

    def test_get_lesson_cards_card_structure(self, client: TestClient, test_db: Session, sample_deck_tree):
        """Test GET /api/v1/decks/{lesson_id}/cards returns cards with correct fields."""
        # Arrange
        lesson_id = sample_deck_tree["lesson"].id

        # Act
        response = client.get(f"/api/v1/decks/{lesson_id}/cards")

        # Assert
        data = response.json()["data"]
        card = data["cards"][0]

        assert "id" in card
        assert "card_index" in card
        assert "front_text" in card
        assert "back_text" in card
        assert "audio_path" in card

    def test_get_lesson_cards_correct_content(self, client: TestClient, test_db: Session, sample_deck_tree):
        """Test GET /api/v1/decks/{lesson_id}/cards returns correct card content."""
        # Arrange
        lesson_id = sample_deck_tree["lesson"].id

        # Act
        response = client.get(f"/api/v1/decks/{lesson_id}/cards")

        # Assert
        data = response.json()["data"]
        card = data["cards"][0]

        assert card["front_text"] == "Last week I went to the theatre."
        assert card["back_text"] == "上周我去了剧院。"
        audio_path = card["audio_path"]
        assert isinstance(audio_path, str)
        assert (
            "audio/nce2/unit1/lesson1/0.wav" in audio_path
            or "audio%2Fnce2%2Funit1%2Flesson1%2F0.wav" in audio_path
        )
        assert card["card_index"] == 0

    def test_get_lesson_cards_ordered_by_index(self, client: TestClient, test_db: Session, sample_deck_tree):
        """Test GET /api/v1/decks/{lesson_id}/cards returns cards in correct order."""
        # Arrange
        lesson_id = sample_deck_tree["lesson"].id

        # Act
        response = client.get(f"/api/v1/decks/{lesson_id}/cards")

        # Assert
        data = response.json()["data"]
        cards = data["cards"]

        for i in range(len(cards) - 1):
            assert cards[i]["card_index"] < cards[i + 1]["card_index"]

    def test_get_lesson_cards_lesson_not_found(self, client: TestClient, test_db: Session):
        """Test GET /api/v1/decks/{lesson_id}/cards returns 404 for non-existent lesson."""
        # Arrange
        non_existent_lesson_id = 99999

        # Act
        response = client.get(f"/api/v1/decks/{non_existent_lesson_id}/cards")

        # Assert
        assert response.status_code == 404

    def test_get_lesson_cards_not_found_error_structure(self, client: TestClient, test_db: Session):
        """Test GET /api/v1/decks/{lesson_id}/cards returns proper error structure for 404."""
        # Arrange
        non_existent_lesson_id = 99999

        # Act
        response = client.get(f"/api/v1/decks/{non_existent_lesson_id}/cards")

        # Assert
        assert response.status_code == 404
        data = response.json()

        assert "detail" in data
        detail = data["detail"]
        assert "request_id" in detail
        assert "error" in detail

        error = detail["error"]
        assert "code" in error
        assert "message" in error
        assert error["code"] == "LESSON_NOT_FOUND"

    def test_get_lesson_cards_wrong_deck_type(self, client: TestClient, test_db: Session, sample_deck_tree):
        """Test GET /api/v1/decks/{lesson_id}/cards returns 404 for non-lesson deck."""
        # Arrange
        unit_id = sample_deck_tree["unit"].id  # Unit, not lesson

        # Act
        response = client.get(f"/api/v1/decks/{unit_id}/cards")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"]["code"] == "LESSON_NOT_FOUND"

    def test_get_lesson_cards_empty_lesson(self, client: TestClient, test_db: Session):
        """Test GET /api/v1/decks/{lesson_id}/cards returns empty cards list for lesson with no cards."""
        # Arrange
        from app.models import Deck

        source = Deck(title="Test Source", type="source", level_index=0)
        test_db.add(source)
        test_db.flush()

        unit = Deck(title="Test Unit", type="unit", level_index=0, parent_id=source.id)
        test_db.add(unit)
        test_db.flush()

        empty_lesson = Deck(title="Empty Lesson", type="lesson", level_index=0, parent_id=unit.id)
        test_db.add(empty_lesson)
        test_db.commit()

        # Act
        response = client.get(f"/api/v1/decks/{empty_lesson.id}/cards")

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["cards"] == []

    def test_get_lesson_cards_invalid_lesson_id_type(self, client: TestClient, test_db: Session):
        """Test GET /api/v1/decks/{lesson_id}/cards handles invalid lesson_id type."""
        # Act
        response = client.get("/api/v1/decks/invalid/cards")

        # Assert
        assert response.status_code == 422  # Unprocessable Entity (validation error)
