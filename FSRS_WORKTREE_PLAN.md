# LanGear FSRS Worktree Plan

## Worktree
- Branch: `wt/fsrs-study-session-backend`
- Path: `/Users/mepuru/Desktop/project/langear/LanGear-wt-fsrs-study-session-backend`
- Purpose: implement the backend learning-session entrypoint and Beijing-time scheduling semantics without touching the rating endpoint contract

## Goal
Deliver a backend-only learning scheduling flow centered on `GET /api/v1/study/session`.

Success means:
- `/decks/{lesson_id}/cards` stays a pure browsing/content API
- a new study-session API returns cards selected by FSRS state, scope, due-ness, and quota
- all business time calculations use `Asia/Shanghai`
- dashboard “today / streak / heatmap” logic is aligned with the same Beijing-time rules

## In Scope
- `backend/app/repositories/srs_repo.py`
- `backend/app/repositories/card_repo.py`
- `backend/app/repositories/deck_repo.py`
- `backend/app/repositories/review_log_repo.py`
- `backend/app/services/dashboard_service.py`
- `backend/app/services/settings_service.py` if needed for scope fallback
- `backend/app/services/study_session_service.py` (new)
- `backend/app/routers/study_session.py` (new)
- `backend/app/main.py`
- backend tests for repositories, dashboard, and the new study-session route

## Out of Scope
- integer rating contract changes in `POST /study/submissions/{id}/rating`
- frontend consumption of `/api/v1/study/session`
- README / PRD / PRD_BASELINE updates

## Required Decisions Already Locked
- Public learning entrypoint is `GET /api/v1/study/session`
- Timezone is `Asia/Shanghai` for business interpretation and API output
- Scope priority:
  1. request `source_scope`
  2. settings `default_source_scope`
  3. all sources
- Scheduling priority:
  1. due `learning` / `relearning`
  2. due `review`
  3. `new`
- Quota consumption:
  1. review cards use `daily_review_limit`
  2. new cards use `daily_new_limit`

## API Contract To Implement
`GET /api/v1/study/session`

Supported query params:
- `source_scope`: optional comma-separated source deck ids
- `lesson_id`: optional lesson restriction while still using scheduling semantics

Response minimum shape:
- `server_time`
- `session_date`
- `scope`
- `quota`
- `summary`
  - `new_remaining`
  - `review_remaining`
  - `due_count`
- `cards[]`
  - `id`
  - `lesson_id`
  - `card_index`
  - `front_text`
  - `back_text`
  - `audio_path`
  - `oss_audio_path`
  - `card_state`
  - `due_at`

Time fields returned by this endpoint must be ISO 8601 with `+08:00`.

## Implementation Steps
1. Introduce shared Beijing-time utilities.
   - Add a small backend helper for:
     - current Shanghai datetime
     - current Shanghai calendar date
     - UTC <-> Shanghai conversion
   - Use it everywhere in this worktree instead of raw `datetime.utcnow()`.

2. Extend repository query capability.
   - `SRSRepository`: due-card queries, per-state filters, and counts that exclude `new` from due counts.
   - `CardRepository` / `DeckRepository`: scope-based card retrieval and lesson/source relationship helpers.
   - `ReviewLogRepository`: date-bounded counting aligned to Beijing day windows.

3. Implement `StudySessionService`.
   - Resolve effective scope.
   - Resolve today’s remaining quotas.
   - Query due review cards first, then new cards.
   - Build response objects with `card_state` and `due_at`.
   - Respect optional `lesson_id` without falling back to content-browsing semantics.

4. Add `backend/app/routers/study_session.py`.
   - Parse and validate `source_scope`.
   - Return the structured session payload.
   - Keep error responses consistent with existing API style.

5. Update `main.py`.
   - Register the new router cleanly.
   - Do not overload `study.py`.

6. Update dashboard logic.
   - Convert “today”, streak, and heatmap date windows to Beijing time.
   - Keep response shape compatible unless a test proves a field contract mismatch.

## Acceptance Checklist
- `/api/v1/study/session` exists and returns cards selected by scheduling, not raw lesson order
- `/api/v1/decks/{lesson_id}/cards` remains untouched
- `due_count` excludes pure new cards
- `source_scope` request override works
- `default_source_scope` fallback works
- returned `server_time` and `due_at` include `+08:00`
- dashboard “today” counts shift with Beijing day boundaries, not UTC midnight

## Suggested Commands
```bash
cd /Users/mepuru/Desktop/project/langear/LanGear-wt-fsrs-study-session-backend/backend
uv run pytest tests/unit/repositories/test_srs_repo.py
uv run pytest tests/integration -k "study_session or dashboard"
```

## Handoff Notes
- Merge this worktree after `wt/fsrs-rating-core`.
- Frontend work will consume this API; keep the response stable once tests pass.
- Prefer adding new files over crowding the existing `study.py` router.
