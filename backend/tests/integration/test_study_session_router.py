"""Integration tests for the study-session API."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Card, Deck, ReviewLog, Setting, UserCardSRS


def _create_scoped_source(
    db: Session,
    title: str,
    source_index: int,
    lesson_index: int,
    state: str = "review",
) -> dict[str, Deck | Card]:
    source = Deck(title=title, type="source", level_index=source_index)
    db.add(source)
    db.flush()

    unit = Deck(title=f"{title} Unit", type="unit", level_index=0, parent_id=source.id)
    db.add(unit)
    db.flush()

    lesson = Deck(title=f"{title} Lesson", type="lesson", level_index=lesson_index, parent_id=unit.id)
    db.add(lesson)
    db.flush()

    card = Card(
        deck_id=lesson.id,
        card_index=0,
        front_text=f"{title} sentence",
        back_text=f"{title} 翻译",
        audio_path=f"audio/{title}.wav",
    )
    db.add(card)
    db.flush()

    db.add(
        UserCardSRS(
            card_id=card.id,
            state=state,
            step=0 if state in {"learning", "relearning"} else None,
            stability=None if state == "learning" else 3.0,
            difficulty=None if state == "learning" else 4.0,
            due=datetime.utcnow() - timedelta(hours=1),
            last_review=None if state == "learning" else datetime.utcnow() - timedelta(days=1),
        )
    )
    db.commit()

    return {"source": source, "lesson": lesson, "card": card}


@pytest.mark.integration
class TestStudySessionRouter:
    def test_get_study_session_prioritizes_due_review_then_new(
        self,
        client: TestClient,
        test_db: Session,
        sample_deck_tree,
    ):
        """GET /study/session should order learning -> review -> new and use +08:00 times."""
        lesson = sample_deck_tree["lesson"]
        cards = sample_deck_tree["cards"]

        test_db.add_all(
            [
                Setting(key="daily_new_limit", value=2),
                Setting(key="daily_review_limit", value=3),
            ]
        )

        srs_rows = test_db.query(UserCardSRS).order_by(UserCardSRS.card_id).all()
        srs_rows[0].state = "learning"
        srs_rows[0].step = 1
        srs_rows[0].due = datetime.utcnow() - timedelta(hours=2)
        srs_rows[0].last_review = datetime.utcnow() - timedelta(hours=3)
        srs_rows[1].state = "review"
        srs_rows[1].step = None
        srs_rows[1].stability = 3.5
        srs_rows[1].difficulty = 4.0
        srs_rows[1].due = datetime.utcnow() - timedelta(hours=1)
        srs_rows[1].last_review = datetime.utcnow() - timedelta(days=1)
        srs_rows[2].state = "review"
        srs_rows[2].step = None
        srs_rows[2].stability = 3.5
        srs_rows[2].difficulty = 4.0
        srs_rows[2].due = datetime.utcnow() + timedelta(days=1)
        srs_rows[2].last_review = datetime.utcnow() - timedelta(days=1)

        test_db.add(
            ReviewLog(
                card_id=cards[0].id,
                deck_id=lesson.id,
                rating="good",
                result_type="single",
                status="completed",
                ai_feedback_json={"oss_path": "recordings/20260321/example.webm"},
            )
        )
        test_db.commit()

        response = client.get(f"/api/v1/study/session?lesson_id={lesson.id}")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["summary"]["due_count"] == 2
        assert [card["card_state"] for card in data["cards"]] == ["learning", "review", "new", "new"]
        assert data["cards"][0]["oss_audio_path"] == "recordings/20260321/example.webm"
        assert datetime.fromisoformat(data["server_time"]).utcoffset() == timedelta(hours=8)
        assert all(
            datetime.fromisoformat(card["due_at"]).utcoffset() == timedelta(hours=8)
            for card in data["cards"]
        )

    def test_get_study_session_source_scope_overrides_settings(
        self,
        client: TestClient,
        test_db: Session,
        sample_deck_tree,
    ):
        """Request source_scope should beat default_source_scope settings."""
        source1 = sample_deck_tree["source"]
        source2_tree = _create_scoped_source(test_db, "Source 2", 1, 0)

        test_db.add(Setting(key="default_source_scope", value=[source2_tree["source"].id]))
        test_db.commit()

        response = client.get(f"/api/v1/study/session?source_scope={source1.id}")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["scope"]["source_ids"] == [source1.id]
        assert all(card["lesson_id"] == sample_deck_tree["lesson"].id for card in data["cards"])

    def test_get_study_session_uses_default_source_scope_when_request_missing(
        self,
        client: TestClient,
        test_db: Session,
        sample_deck_tree,
    ):
        """Settings default_source_scope should apply when request scope is absent."""
        _ = sample_deck_tree
        source2_tree = _create_scoped_source(test_db, "Scoped Source", 1, 0)

        test_db.add_all(
            [
                Setting(key="daily_new_limit", value=0),
                Setting(key="daily_review_limit", value=5),
                Setting(key="default_source_scope", value=[source2_tree["source"].id]),
            ]
        )
        test_db.commit()

        response = client.get("/api/v1/study/session")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["scope"]["source_ids"] == [source2_tree["source"].id]
        assert [card["lesson_id"] for card in data["cards"]] == [source2_tree["lesson"].id]

    def test_get_study_session_rejects_invalid_source_scope(
        self,
        client: TestClient,
        sample_deck_tree,
    ):
        """Invalid source_scope values should return a structured 400."""
        _ = sample_deck_tree

        response = client.get("/api/v1/study/session?source_scope=1,abc")

        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error"]["code"] == "INVALID_SOURCE_SCOPE"
