# LanGear Architecture Reference

This reference summarizes the current logic observed from the local frontend repository and the production backend under `ssh langear-prod:/srv/langear` on 2026-04-29.

## Entry Points

Frontend routes live in `frontend/src/router/index.ts`:

- `/dashboard` loads dashboard stats and deck tree.
- `/library` shows the content library.
- `/study/:lessonId` runs the fullscreen retelling session.
- `/cards/:cardId`, `/summary/:lessonId`, and `/settings` handle secondary views.

Backend routers are registered in production `backend/app/main.py`:

- `/api/v1/health`
- `/api/v1/oss`
- `/api/v1/decks`
- `/api/v1/realtime`
- `/api/v1/study`
- `/api/v1/study/session`
- `/api/v1/dashboard`
- `/api/v1/settings`

## Frontend Study Flow

Primary files:

- `frontend/src/views/StudySessionView.vue`
- `frontend/src/stores/study.ts`
- `frontend/src/stores/studyTasks.ts`
- `frontend/src/composables/useRealtimeAsr.ts`
- `frontend/src/composables/useRecorder.ts`
- `frontend/src/services/api/study.ts`

Current sequence:

1. Route `/study/:lessonId` calls `studyStore.loadStudySession(lessonId)`.
2. `loadStudySession` requests `GET /study/session` with `lesson_id` and maps backend cards into the domain `Card` shape.
3. `studyTasks.initializeLesson` creates one task entry per card, then `restoreLessonHistory` calls `GET /study/submissions?lesson_id=...` to restore latest submission state per card.
4. Starting recording first opens realtime ASR with `useRealtimeAsr.connect(lessonId, cardId)`.
5. The realtime websocket URL is built from `VITE_API_BASE_URL` plus `/realtime/asr/ws`, converted to `ws` or `wss`, and includes `lesson_id` and `card_id`.
6. The browser recorder streams PCM chunks to `useRealtimeAsr.appendAudioChunk` and also collects a WebM blob for upload.
7. Stopping recording calls `realtimeAsr.commit()` and requires a non-empty final transcript before allowing flip.
8. Flipping the card uploads the WebM to OSS via STS credentials from `GET /oss/sts-token`.
9. After upload, the frontend submits `POST /study/submissions` with `lesson_id`, `card_id`, `oss_audio_path`, and `realtime_session_id`.
10. `studyTasks.registerSubmission` starts polling `GET /study/submissions/{id}` every `VITE_POLLING_INTERVAL` or 1500 ms, stopping after `VITE_POLLING_TIMEOUT` or 30000 ms.
11. Completed polling results populate `lastFeedback`, the transcript, and a signed user audio URL.
12. Rating buttons stay disabled until async state is `completed`; rating calls `POST /study/submissions/{id}/rating` and updates local FSRS card state.

## Frontend API Contract Notes

- `frontend/src/services/http.ts` unwraps backend response envelopes. Backend returns `{ request_id, data }`; frontend consumers receive the inner `data`.
- Error extraction expects FastAPI errors at `response.data.detail.error` or direct `response.data.error`.
- `SubmitReviewRequest` in `frontend/src/types/api.ts` includes optional `transcription_text` for mock compatibility. The production backend request model currently requires only `lesson_id`, `card_id`, `oss_audio_path`, and `realtime_session_id`; extra fields are ignored by Pydantic defaults.
- `PollingResponseCompleted.feedback` expects `overall_rating`, `issues`, and optional compatibility fields. Production Gemini normalization currently emits `overall_rating`, `issues`, and `alternative phrases and sentences`.
- `StudyTaskEntry.reviewStatus` is one of `idle`, `submitting`, `processing`, `completed`, or `failed`.

## Production Backend Study Flow

Primary files:

- `/srv/langear/backend/app/routers/realtime.py`
- `/srv/langear/backend/app/services/realtime_session_service.py`
- `/srv/langear/backend/app/routers/oss.py`
- `/srv/langear/backend/app/routers/study.py`
- `/srv/langear/backend/app/services/review_service.py`
- `/srv/langear/backend/app/tasks/review_task.py`
- `/srv/langear/backend/app/adapters/gemini_adapter.py`
- `/srv/langear/backend/app/adapters/oss_adapter.py`

Current sequence:

1. `GET /oss/sts-token` returns temporary STS credentials for frontend direct upload to the normalized recordings prefix.
2. `WebSocket /realtime/asr/ws` creates an in-memory realtime session with `lesson_id`, `card_id`, model, status, partial text, final text, and TTL metadata.
3. With provider `dashscope`, `DashScopeRealtimeASRBridge` connects to DashScope Omni realtime, forwards frontend audio chunks, and forwards transcription callbacks back to the browser.
4. When DashScope reports final transcription, the backend marks the realtime session `ready` with final text.
5. `POST /study/submissions` calls `ReviewService.submit_card_review`.
6. `ReviewService` validates the card exists, belongs to the lesson, the OSS path starts with the configured recordings prefix, and the realtime session exists, matches lesson/card, is not failed, is `ready`, and has final text.
7. The service stores a `review_log` with `status="processing"` and study-session metadata, commits it, then starts a daemon thread for `process_review_task`.
8. `process_review_task` signs the user audio URL and reference audio URL, verifies realtime final text is non-empty, then calls the AI feedback provider.
9. Gemini feedback generation downloads both signed audio URLs and sends them to the official `google-genai` SDK as inline audio parts.
10. The task stores `transcription`, `feedback`, `oss_path`, `realtime_session_id`, and `reference_audio_path` into `review_log.ai_feedback_json`, then marks status `completed`.
11. Polling returns `processing`, `failed`, or `completed`. SRS data is only included after a rating exists.
12. `POST /study/submissions/{submission_id}/rating` normalizes numeric or string ratings, updates FSRS through `FSRSAdapter`, writes FSRS review log data, and stores the rating on the `review_log`.

## Scheduling and Content

- `StudySessionService.get_session` builds the study queue from default source scope or requested scope, applies daily new and review limits, then orders learning/relearning, review, new, and lesson-scoped reviewed cards.
- New cards are derived from missing SRS rows or new-bucket state; native FSRS states exposed to the frontend are `learning`, `review`, and `relearning`.
- Lesson-scoped study pages deliberately retain reviewed lesson cards after refresh, while global study sessions focus on the due queue.
- `ContentService.get_deck_tree` returns sources, units, and lessons with total, completed, due, and new counts.
- Reference audio paths are signed by `OSSAdapter.generate_signed_url`; signing failures are swallowed for session/card lists to avoid failing the whole response.

## Dashboard and Settings

- Production `DashboardService.get_dashboard_stats` returns the legacy shape: `today`, `streak_days`, and `heatmap`.
- Local `frontend/src/stores/dashboard.ts` normalizes the legacy backend shape into the richer frontend `DashboardData` shape used by the dashboard components.
- Settings are loaded through the settings router and affect daily new/review limits and default source scope.

## Deployment and Runtime

- Production SSH alias: `ssh langear-prod`.
- Deployment root: `/srv/langear`.
- Compose files: `/srv/langear/docker-compose.yml` and `/srv/langear/docker-compose.server.yml`.
- Production backend data bind mount: `/srv/langear/data` to `/app/data`.
- Backend service command stack uses migration, seed, then backend service.
- `/srv/langear` may not be a git repository. Do local git operations in the workspace unless deployment work is explicitly requested.

Useful production commands:

```bash
ssh langear-prod 'cd /srv/langear && docker compose -f docker-compose.yml -f docker-compose.server.yml ps'
ssh langear-prod 'cd /srv/langear && docker compose -f docker-compose.yml -f docker-compose.server.yml logs --tail=200 backend'
ssh langear-prod 'cd /srv/langear && sed -n "1,260p" backend/app/routers/study.py'
```

## Common Error Surfaces

- `REALTIME_SESSION_NOT_FOUND`: session id missing, expired, process-local store mismatch, or lesson/card mismatch.
- `REALTIME_TRANSCRIPT_NOT_READY`: frontend submitted before final transcript reached backend ready state, or commit produced empty transcript.
- `REALTIME_SESSION_FAILED`: websocket/DashScope bridge failed, invalid audio append, or session marked failed before submit.
- `INVALID_OSS_PATH`: uploaded object does not start with configured recordings prefix.
- `USER_AUDIO_ACCESS_FAILED`: backend could not sign or access the uploaded user audio.
- `REFERENCE_AUDIO_NOT_FOUND`: card has no reference audio path or backend cannot sign/access it.
- `AI_FEEDBACK_FAILED`: Gemini request, audio download, JSON parsing, or schema normalization failed.
- Frontend polling timeout: client stopped polling after its configured timeout, but backend task may still complete later and be restorable via submission history.

## Investigation Checklist

For recording, upload, ASR, or feedback issues:

1. Confirm frontend state transitions in `StudySessionView.vue`, especially recording, commit, flip, upload, submit, and polling.
2. Confirm request payloads in `frontend/src/services/api/study.ts` and types in `frontend/src/types/api.ts`.
3. Read production `routers/realtime.py` and `services/realtime_session_service.py` for session lifecycle.
4. Read production `ReviewService.submit_card_review` for validation failures before a `review_log` is committed.
5. Read production `process_review_task` for failures after a submission id exists.
6. Check backend logs by request id, submission id, realtime session id, card id, lesson id, and OSS path.
7. Only after the issue location is clear, propose a code change and the smallest relevant test.

For dashboard, deck, or scheduling issues:

1. Inspect `frontend/src/stores/dashboard.ts`, `frontend/src/stores/deck.ts`, and deck/dashboard components.
2. Inspect production `services/dashboard_service.py`, `services/content_service.py`, and `services/study_session_service.py`.
3. Compare legacy backend shapes with frontend normalization logic.
4. Verify whether the issue is data, SRS schedule, timezone, response envelope, or UI mapping.

For prompt or Gemini output-shape changes:

1. Use the separate `langear-prompt-update` skill.
2. Keep prompt schema, backend normalization, frontend feedback rendering, and tests aligned.
