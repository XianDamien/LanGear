"""Integration tests for study submissions API.

Tests:
- POST /api/v1/study/submissions (create async feedback job)
- GET /api/v1/study/submissions/{id} (poll result)
- POST /api/v1/study/submissions/{id}/rating (submit FSRS rating)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.review_log import ReviewLog


@pytest.mark.integration
class TestStudyRouter:
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

        lesson_id = sample_deck_tree["lesson"].id
        card_id = sample_deck_tree["cards"][0].id

        create_resp = client.post(
            "/api/v1/study/submissions",
            json={
                "lesson_id": lesson_id,
                "card_id": card_id,
                "oss_audio_path": "recordings/20260209/test.webm",
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

    def test_get_submission_completed_includes_issues(
        self,
        client: TestClient,
        test_db: Session,
        sample_deck_tree,
    ):
        """GET /study/submissions/{id} should include feedback.issues field."""
        lesson_id = sample_deck_tree["lesson"].id
        card_id = sample_deck_tree["cards"][0].id

        review_log = ReviewLog(
            card_id=card_id,
            deck_id=lesson_id,
            rating=None,
            result_type="single",
            status="completed",
            ai_feedback_json={
                "transcription": {
                    "text": "Last week I went to the theatre.",
                    "timestamps": [],
                },
                "feedback": {
                    "pronunciation": "Good",
                    "completeness": "Complete",
                    "fluency": "Fluent",
                    "suggestions": [],
                    "issues": [
                        {"problem": "Missing ending sound", "timestamp": 0.9}
                    ],
                },
                "oss_path": "recordings/20260319/test.webm",
            },
        )
        test_db.add(review_log)
        test_db.commit()
        test_db.refresh(review_log)

        resp = client.get(f"/api/v1/study/submissions/{review_log.id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "completed"
        assert "issues" in data["feedback"]
        assert data["feedback"]["issues"][0]["timestamp"] == 0.9
