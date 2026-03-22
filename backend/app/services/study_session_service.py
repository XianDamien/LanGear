"""Study-session scheduling service."""

from typing import Any

from sqlalchemy.orm import Session

from app.adapters.oss_adapter import OSSAdapter
from app.repositories.card_repo import CardRepository
from app.repositories.deck_repo import DeckRepository
from app.repositories.review_log_repo import ReviewLogRepository
from app.repositories.settings_repo import SettingsRepository
from app.repositories.srs_repo import SRSRepository
from app.utils.timezone import shanghai_now, to_shanghai, to_storage_utc


class StudySessionService:
    """Build a scheduled study session from FSRS state and quota rules."""

    def __init__(self, db: Session):
        """Initialize service dependencies."""
        self.db = db
        self.card_repo = CardRepository(db)
        self.deck_repo = DeckRepository(db)
        self.review_log_repo = ReviewLogRepository(db)
        self.settings_repo = SettingsRepository(db)
        self.srs_repo = SRSRepository(db)
        self.oss_adapter = OSSAdapter()

    def get_session(
        self,
        source_scope: list[int] | None = None,
        lesson_id: int | None = None,
    ) -> dict[str, Any]:
        """Build the current study session payload."""
        server_time = shanghai_now()
        business_date = server_time.date()
        as_of = to_storage_utc(server_time)

        effective_scope = self._resolve_effective_scope(source_scope)
        lesson_ids = self._resolve_lesson_ids(effective_scope, lesson_id)

        settings = self.settings_repo.get_all()
        daily_new_limit = settings.get("daily_new_limit", 20)
        daily_review_limit = settings.get("daily_review_limit", 100)

        quota_usage = self.review_log_repo.count_quota_usage_by_date(business_date)
        new_remaining = max(0, daily_new_limit - quota_usage["new"])
        review_remaining = max(0, daily_review_limit - quota_usage["review"])

        due_learning = self.srs_repo.get_due_cards(
            lesson_ids=lesson_ids,
            states=["learning", "relearning"],
            limit=review_remaining,
            as_of=as_of,
        )
        review_slots_left = max(0, review_remaining - len(due_learning))
        due_review = self.srs_repo.get_due_cards(
            lesson_ids=lesson_ids,
            states=["review"],
            limit=review_slots_left,
            as_of=as_of,
        )
        new_cards = self.card_repo.get_new_cards(
            lesson_ids=lesson_ids,
            limit=new_remaining,
        )

        due_count = self.srs_repo.count_due_cards(lesson_ids=lesson_ids, as_of=as_of)
        latest_oss_paths = self.review_log_repo.get_latest_oss_paths_by_lesson_ids(lesson_ids)

        cards = [
            *[
                self._serialize_card(card, srs, latest_oss_paths.get(card.id), server_time)
                for card, srs in due_learning
            ],
            *[
                self._serialize_card(card, srs, latest_oss_paths.get(card.id), server_time)
                for card, srs in due_review
            ],
            *[
                self._serialize_card(card, srs, latest_oss_paths.get(card.id), server_time)
                for card, srs in new_cards
            ],
        ]

        lesson_name = None
        if lesson_id is not None:
            lesson = self.deck_repo.get_by_id(lesson_id)
            lesson_name = lesson.title if lesson is not None else None

        return {
            "server_time": server_time.isoformat(),
            "session_date": business_date.isoformat(),
            "scope": {
                "source_ids": effective_scope,
                "lesson_id": lesson_id,
            },
            "quota": {
                "daily_new_limit": daily_new_limit,
                "daily_review_limit": daily_review_limit,
                "new_remaining": new_remaining,
                "review_remaining": review_remaining,
            },
            "summary": {
                "new_remaining": new_remaining,
                "review_remaining": review_remaining,
                "due_count": due_count,
            },
            "cards": cards,
            "lesson_name": lesson_name,
        }

    def _resolve_effective_scope(self, requested_scope: list[int] | None) -> list[int]:
        """Resolve effective source scope using request, settings, then all sources."""
        if requested_scope is not None:
            source_ids = self._validated_source_ids(requested_scope)
            if len(source_ids) != len(set(requested_scope)):
                raise ValueError("Invalid source_scope: one or more source decks do not exist")
            return source_ids

        settings = self.settings_repo.get_all()
        default_scope = settings.get("default_source_scope")
        if isinstance(default_scope, list) and default_scope:
            source_ids = self._validated_source_ids(default_scope)
            if source_ids:
                return source_ids

        return [source.id for source in self.deck_repo.get_all_sources()]

    def _validated_source_ids(self, scope_ids: list[int]) -> list[int]:
        """Return de-duplicated valid source IDs preserving request order."""
        deduped_ids: list[int] = []
        seen: set[int] = set()
        for deck_id in scope_ids:
            if deck_id not in seen:
                seen.add(deck_id)
                deduped_ids.append(deck_id)

        valid_sources = self.deck_repo.get_sources_by_ids(deduped_ids)
        valid_source_ids = {source.id for source in valid_sources}
        return [deck_id for deck_id in deduped_ids if deck_id in valid_source_ids]

    def _resolve_lesson_ids(self, source_ids: list[int], lesson_id: int | None) -> list[int]:
        """Resolve lesson IDs from scope and optional lesson restriction."""
        if lesson_id is not None:
            lesson = self.deck_repo.get_by_id(lesson_id)
            if lesson is None or lesson.type != "lesson":
                raise LookupError(f"Lesson {lesson_id} not found")

            lesson_source_id = self.deck_repo.get_source_id_for_lesson(lesson_id)
            if lesson_source_id is None or lesson_source_id not in source_ids:
                return []
            return [lesson_id]

        return self.deck_repo.get_lesson_ids_for_sources(source_ids)

    def _safe_signed_audio_url(self, audio_path: str | None) -> str | None:
        """Sign reference audio URLs without failing the whole session response."""
        if not audio_path:
            return None
        try:
            return self.oss_adapter.generate_signed_url(audio_path, expires=7200)
        except Exception:
            return None

    def _serialize_card(
        self,
        card: Any,
        srs: Any,
        latest_oss_path: str | None,
        server_time: Any,
    ) -> dict[str, Any]:
        """Serialize a card row for the study session response."""
        card_state = srs.state if srs is not None else "new"
        due_at = to_shanghai(srs.due) if srs is not None else server_time

        return {
            "id": card.id,
            "lesson_id": card.deck_id,
            "card_index": card.card_index,
            "front_text": card.front_text,
            "back_text": card.back_text,
            "audio_path": self._safe_signed_audio_url(card.audio_path),
            "oss_audio_path": latest_oss_path,
            "card_state": card_state,
            "due_at": due_at.isoformat(),
        }
