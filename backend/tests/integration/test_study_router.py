"""Integration tests for study submissions API.

Tests:
- POST /api/v1/study/submissions (create async feedback job)
- GET /api/v1/study/submissions/{id} (poll result)
- POST /api/v1/study/submissions/{id}/rating (submit FSRS rating)
"""

import base64

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.realtime_session_service import get_realtime_session_store


def _make_ready_realtime_session(lesson_id: int, card_id: int) -> str:
    store = get_realtime_session_store()
    session = store.create_session(
        lesson_id=lesson_id,
        card_id=card_id,
        model="qwen3-asr-flash-realtime",
    )
    sample_chunk = base64.b64encode(b"fake-audio-bytes").decode("utf-8")
    store.append_audio_chunk(session.id, sample_chunk)
    store.commit_session(session.id)
    return session.id


@pytest.mark.integration
class TestStudyRouter:
    def test_submit_submission_requires_realtime_session_id(
        self,
        client: TestClient,
        sample_deck_tree,
        monkeypatch,
    ):
        """POST /study/submissions should reject requests without realtime_session_id."""

        # Avoid launching a real background thread in tests.
        class _FakeThread:
            def __init__(self, target=None, args=(), daemon=None):
                self.target = target
                self.args = args
                self.daemon = daemon

            def start(self):
                return None

        monkeypatch.setattr("app.services.review_service.threading.Thread", _FakeThread)

        lesson_id = sample_deck_tree["lesson"].id
        card_id = sample_deck_tree["cards"][0].id

        resp = client.post(
            "/api/v1/study/submissions",
            json={
                "lesson_id": lesson_id,
                "card_id": card_id,
                "oss_audio_path": "recordings/20260209/test.webm",
            },
        )

        assert resp.status_code == 422

    def test_submit_submission_realtime_not_ready(
        self,
        client: TestClient,
        sample_deck_tree,
        monkeypatch,
    ):
        """POST /study/submissions should block when realtime session is not ready."""

        class _FakeThread:
            def __init__(self, target=None, args=(), daemon=None):
                self.target = target
                self.args = args
                self.daemon = daemon

            def start(self):
                return None

        monkeypatch.setattr("app.services.review_service.threading.Thread", _FakeThread)

        store = get_realtime_session_store()
        store.clear()

        lesson_id = sample_deck_tree["lesson"].id
        card_id = sample_deck_tree["cards"][0].id
        session = store.create_session(
            lesson_id=lesson_id,
            card_id=card_id,
            model="qwen3-asr-flash-realtime",
        )

        resp = client.post(
            "/api/v1/study/submissions",
            json={
                "lesson_id": lesson_id,
                "card_id": card_id,
                "oss_audio_path": "recordings/20260209/test.webm",
                "realtime_session_id": session.id,
            },
        )

        assert resp.status_code == 400
        assert resp.json()["detail"]["error"]["code"] == "REALTIME_TRANSCRIPT_NOT_READY"

    def test_submit_submission_realtime_failed(
        self,
        client: TestClient,
        sample_deck_tree,
        monkeypatch,
    ):
        """POST /study/submissions should block when realtime session failed."""

        class _FakeThread:
            def __init__(self, target=None, args=(), daemon=None):
                self.target = target
                self.args = args
                self.daemon = daemon

            def start(self):
                return None

        monkeypatch.setattr("app.services.review_service.threading.Thread", _FakeThread)

        store = get_realtime_session_store()
        store.clear()

        lesson_id = sample_deck_tree["lesson"].id
        card_id = sample_deck_tree["cards"][0].id
        session = store.create_session(
            lesson_id=lesson_id,
            card_id=card_id,
            model="qwen3-asr-flash-realtime",
        )
        store.mark_session_failed(session.id, "manual failure")

        resp = client.post(
            "/api/v1/study/submissions",
            json={
                "lesson_id": lesson_id,
                "card_id": card_id,
                "oss_audio_path": "recordings/20260209/test.webm",
                "realtime_session_id": session.id,
            },
        )

        assert resp.status_code == 400
        assert resp.json()["detail"]["error"]["code"] == "REALTIME_SESSION_FAILED"

    def test_submit_submission_without_rating_success(
        self,
        client: TestClient,
        test_db: Session,
        sample_deck_tree,
        all_adapters_mocked,
        monkeypatch,
    ):
        """POST /study/submissions should accept payload without rating."""

        # Avoid launching a real background thread in tests.
        class _FakeThread:
            def __init__(self, target=None, args=(), daemon=None):
                self.target = target
                self.args = args
                self.daemon = daemon

            def start(self):
                return None

        monkeypatch.setattr("app.services.review_service.threading.Thread", _FakeThread)

        store = get_realtime_session_store()
        store.clear()

        lesson_id = sample_deck_tree["lesson"].id
        card_id = sample_deck_tree["cards"][0].id
        realtime_session_id = _make_ready_realtime_session(lesson_id, card_id)

        resp = client.post(
            "/api/v1/study/submissions",
            json={
                "lesson_id": lesson_id,
                "card_id": card_id,
                "oss_audio_path": "recordings/20260209/test.webm",
                "realtime_session_id": realtime_session_id,
            },
        )

        assert resp.status_code == 200
        body = resp.json()
        assert "request_id" in body
        assert body["data"]["status"] == "processing"
        assert isinstance(body["data"]["submission_id"], int)

    def test_submit_rating_updates_srs(
        self,
        client: TestClient,
        test_db: Session,
        sample_deck_tree,
        all_adapters_mocked,
        monkeypatch,
    ):
        """POST /study/submissions/{id}/rating should update SRS and rating."""

        # Avoid launching a real background thread in tests.
        class _FakeThread:
            def __init__(self, target=None, args=(), daemon=None):
                self.target = target
                self.args = args
                self.daemon = daemon

            def start(self):
                return None

        monkeypatch.setattr("app.services.review_service.threading.Thread", _FakeThread)

        store = get_realtime_session_store()
        store.clear()

        lesson_id = sample_deck_tree["lesson"].id
        card_id = sample_deck_tree["cards"][0].id
        realtime_session_id = _make_ready_realtime_session(lesson_id, card_id)

        create_resp = client.post(
            "/api/v1/study/submissions",
            json={
                "lesson_id": lesson_id,
                "card_id": card_id,
                "oss_audio_path": "recordings/20260209/test.webm",
                "realtime_session_id": realtime_session_id,
            },
        )
        assert create_resp.status_code == 200
        submission_id = create_resp.json()["data"]["submission_id"]

        rate_resp = client.post(
            f"/api/v1/study/submissions/{submission_id}/rating",
            json={"rating": "good"},
        )
        assert rate_resp.status_code == 200
        data = rate_resp.json()["data"]
        assert data["submission_id"] == submission_id
        assert data["rating"] == "good"
        assert "srs" in data
        assert "due" in data["srs"]
